"""OllamaQueue — simplified priority queue for Ollama API calls.

Serializes access to Ollama (single GPU) by processing requests by priority.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import IntEnum
from threading import Event

import ollama as ollama_lib

from app.config import OllamaSettings

logger = logging.getLogger(__name__)
class Priority(IntEnum):
    """Priority levels for Ollama requests (lower = higher priority)."""

    HIGH = 10
    MEDIUM = 50
    LOW = 90
@dataclass(order=True)
class QueueItem:
    """Queue element. Ordered by (priority, sequence)."""

    priority: int
    sequence: int
    request_id: str = field(compare=False)
    kwargs: dict = field(compare=False)
    future: asyncio.Future = field(compare=False)
    cancel_event: Event | None = field(default=None, compare=False)
    enqueued_at: float = field(default_factory=time.time, compare=False)
class OllamaQueue:
    """Priority queue to serialize Ollama API calls."""

    DEFAULT_NUM_CTX = 8192

    def __init__(self):
        self._queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ollama")
        self._sequence = 0
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self.ollama_settings = OllamaSettings()

    async def start(self):
        """Start the async worker."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("OllamaQueue worker started")

    async def stop(self):
        """Stop the worker gracefully."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
        self._executor.shutdown(wait=False)
        logger.info("OllamaQueue worker stopped")

    async def _worker(self):
        """Main loop: process items by priority."""
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                item = await self._queue.get()
            except asyncio.CancelledError:
                break

            if item.cancel_event and item.cancel_event.is_set():
                item.future.set_exception(asyncio.CancelledError())
                self._queue.task_done()
                continue

            logger.info(
                "Processing request %s (priority=%s)",
                item.request_id,
                Priority(item.priority).name,
            )

            try:
                result = await loop.run_in_executor(
                    self._executor, lambda: ollama_lib.chat(**item.kwargs)
                )
                item.future.set_result(result)
            except Exception as exc:
                if not item.future.done():
                    item.future.set_exception(exc)
                logger.exception("Error processing request %s", item.request_id)
            finally:
                self._queue.task_done()

    def _next_sequence(self) -> int:
        """Monotonic counter to guarantee FIFO at equal priority."""
        seq = self._sequence
        self._sequence += 1
        return seq

    async def chat_queued(
        self,
        priority: Priority,
        model: str,
        messages: list,
        temperature: float,
        tools: list | None = None,
        format: dict | None = None,
        cancel_event: Event | None = None,
        num_predict: int | None = None,
    ) -> dict:
        """Submit a non-streaming chat request to the queue and wait for result."""
        options = self.ollama_settings.to_options(temperature)
        if num_predict is not None:
            options["num_predict"] = num_predict
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "options": options,
        }
        if self.ollama_settings.stop:
            kwargs["stop"] = self.ollama_settings.stop
        if tools is not None:
            kwargs["tools"] = tools
        if format is not None:
            kwargs["format"] = format

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        request_id = str(uuid.uuid4())[:8]

        item = QueueItem(
            priority=int(priority),
            sequence=self._next_sequence(),
            request_id=request_id,
            kwargs=kwargs,
            future=future,
            cancel_event=cancel_event,
        )
        await self._queue.put(item)
        logger.debug("Enqueued chat request %s (priority=%s)", request_id, priority.name)

        return await future

    def status(self) -> dict:
        """Return queue status."""
        return {
            "queue_size": self._queue.qsize(),
            "running": self._running,
        }
_queue: OllamaQueue | None = None
def get_queue() -> OllamaQueue:
    """Return the singleton OllamaQueue."""
    global _queue  # noqa: PLW0603
    if _queue is None:
        _queue = OllamaQueue()
    return _queue
def reset_queue():
    """Reset the singleton (for tests)."""
    global _queue  # noqa: PLW0603
    _queue = None
