"""File locking utilities."""

from __future__ import annotations

import msvcrt
import threading
import time
from pathlib import Path


class FileLock:
    """A Windows file lock with a simple cross-process timeout."""

    def __init__(self, lock_path: Path, timeout: float = 10.0):
        self.lock_path = lock_path
        self.timeout = timeout
        self._handle = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()
        while True:
            try:
                self._handle = open(self.lock_path, "w+b")
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except (OSError, BlockingIOError):
                if self._handle is not None:
                    try:
                        self._handle.close()
                    except OSError:
                        pass
                    self._handle = None
                if time.time() - start >= self.timeout:
                    raise TimeoutError(f"Could not acquire lock: {self.lock_path}")
                time.sleep(0.05)

    def release(self) -> None:
        if self._handle is not None:
            try:
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, *_exc) -> None:
        self.release()


class LockManager:
    """Thread/process-friendly lock manager for one data directory."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self._thread_lock = threading.RLock()

    def file_lock(self, name: str = "storage") -> FileLock:
        return FileLock(self.data_dir / f".{name}.lock")

    def __enter__(self) -> "LockManager":
        self._thread_lock.acquire()
        self.file_lock().acquire()
        return self

    def __exit__(self, *_exc) -> None:
        try:
            self.file_lock().release()
        finally:
            self._thread_lock.release()