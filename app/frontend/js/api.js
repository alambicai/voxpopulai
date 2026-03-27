/**
 * API client — REST + SSE streaming.
 */
const API = {
  async get(path) {
    const r = await fetch(`/api${path}`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async post(path, body) {
    const r = await fetch(`/api${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async put(path, body) {
    const r = await fetch(`/api${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async del(path) {
    const r = await fetch(`/api${path}`, { method: "DELETE" });
    if (!r.ok) throw new Error(await r.text());
    if (r.status === 204) return null;
    return r.json();
  },

  stream(path, body, onEvent) {
    const controller = new AbortController();
    let cancelled = false;

    const promise = (async () => {
      const r = await fetch(`/api${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!r.ok) throw new Error(await r.text());
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop();
          for (const part of parts) {
            const line = part.trim();
            if (line.startsWith("data: ")) {
              try { onEvent(JSON.parse(line.slice(6))); } catch { /* skip malformed */ }
            }
          }
        }
        if (buffer.trim().startsWith("data: ")) {
          try { onEvent(JSON.parse(buffer.trim().slice(6))); } catch { /* skip */ }
        }
      } catch (e) {
        if (cancelled) return;
        throw e;
      }
    })();

    return {
      promise,
      cancel() {
        cancelled = true;
        controller.abort();
      },
    };
  },
};
