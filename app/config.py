"""Application configuration — settings persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
class SyntheticSettings(BaseModel):
    """Settings for synthetic population voting."""

    generation_model: str = "qwen3:14b"
    generation_temperature: float = 0.8
    judge_model: str = ""
    judge_temperature: float = 0.1
    judge_max_retries: int = 2
    persona_models: list[str] = ["qwen3:14b"]
    analysis_model: str = "qwen3:14b"
class OllamaSettings(BaseModel):
    """Ollama runtime parameters passed in the options dict of every API call."""

    num_ctx: int | None = 8192
    num_batch: int | None = None
    num_gpu: int | None = None
    main_gpu: int | None = None
    num_thread: int | None = None
    num_predict: int | None = None
    top_k: int | None = None
    top_p: float | None = None
    min_p: float | None = None
    typical_p: float | None = None
    repeat_last_n: int | None = None
    repeat_penalty: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    seed: int | None = None
    stop: list[str] | None = None

    def to_options(self, temperature: float) -> dict:
        """Build the options dict for ollama.chat()."""
        opts: dict = {"temperature": temperature}
        for field_name, value in self.model_dump(exclude_none=True).items():
            if field_name == "stop":
                continue
            opts[field_name] = value
        return opts
class AppSettings(BaseModel):
    """Application settings."""

    synthetic: SyntheticSettings = Field(default_factory=SyntheticSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)

    @staticmethod
    def get_settings_path() -> Path:
        return DATA_DIR / "settings.json"

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from file."""
        path = cls.get_settings_path()
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def save(self) -> None:
        """Save settings to file."""
        path = self.get_settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)
