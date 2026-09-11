import gc
import os
import threading
import time

import stable_whisper
from loguru import logger

MODEL_IDLE_TIMEOUT_SECONDS = int(os.environ.get("MODEL_IDLE_TIMEOUT_SECONDS", 5 * 60))
_EVICT_CHECK_INTERVAL_SECONDS = 30


class _ModelCache:
    """Keeps loaded Whisper models in memory, keyed by model_type.

    Each cached model is evicted independently (freeing RAM/VRAM) after
    MODEL_IDLE_TIMEOUT_SECONDS of not being used, so switching between a
    handful of model sizes doesn't force a reload every time, while
    models nobody's touched in a while still get cleaned up.
    """

    def __init__(self):
        """Start with an empty cache — no models loaded yet."""
        self._models = {}
        self._last_used = {}
        self._lock = threading.Lock()

    def get(self, model_type: str):
        """
        Return the cached model for model_type, loading it if not already cached.

        :param model_type: Whisper model size/name (e.g. "tiny", "large").

        :return: A loaded stable_whisper model instance.
        """
        with self._lock:
            now = time.monotonic()

            if model_type in self._models:
                idle_for = now - self._last_used[model_type]
                self._last_used[model_type] = now
                logger.info(
                    "Reusing cached Whisper model {!r} (was idle for {:.1f}s)",
                    model_type, idle_for,
                )
                return self._models[model_type]

            logger.info("Loading Whisper model {!r}", model_type)
            model = stable_whisper.load_model(model_type)
            self._models[model_type] = model
            self._last_used[model_type] = now
            return model

    def _evict_locked(self, model_type: str):
        """
        Free one cached model by name, caller must already hold self._lock.

        :param model_type: Key of the model to evict. No-op if not cached.
        """
        if model_type not in self._models:
            return
        logger.info("Evicting idle Whisper model {!r} from memory", model_type)
        del self._models[model_type]
        del self._last_used[model_type]
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def evict_idle(self):
        """Evict every cached model that's been idle past MODEL_IDLE_TIMEOUT_SECONDS."""
        with self._lock:
            now = time.monotonic()
            idle_types = [
                model_type
                for model_type, last_used in self._last_used.items()
                if now - last_used > MODEL_IDLE_TIMEOUT_SECONDS
            ]
            for model_type in idle_types:
                self._evict_locked(model_type)


_cache = _ModelCache()


def get_model(model_type: str):
    """Return a loaded Whisper model, reusing a cached one when possible.

    :param model_type: Whisper model size/name (e.g. "tiny", "large").
    :return: A loaded stable_whisper model instance.
    """
    return _cache.get(model_type)


def _idle_eviction_loop():
    """Run forever in the background, periodically evicting idle models."""
    while True:
        time.sleep(_EVICT_CHECK_INTERVAL_SECONDS)
        _cache.evict_idle()


threading.Thread(target=_idle_eviction_loop, daemon=True, name="model-cache-evictor").start()
