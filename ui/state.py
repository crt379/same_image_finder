import sqlite3
from typing import Any

from ui.thread_work import ThreadWorkS


class AppState:

    def __init__(self):
        self.config = None
        self._run_path = None
        self._db_conn = None
        self._threads = None
        self._states = {}
        self._subscribe_k_handles: dict[str, list] = {}

    def set_run_path(self, path: str) -> None:
        self._run_path = path

    def get_run_path(self) -> str | None:
        return self._run_path
    
    def set_db_conn(self, conn: sqlite3.Connection) -> None:
        self._db_conn = conn

    def get_db_conn(self) -> sqlite3.Connection | None:
        return self._db_conn
    
    def set_threads(self, threads: ThreadWorkS):
        self._threads = threads

    def get_threads(self) -> ThreadWorkS | None:
        return self._threads

    def register(self, name, state) -> None:
        self._states[name] = state

    def get_state(self, name) -> Any:
        return self._states.get(name)
    
    def subscribe(self, key, handle) -> None:
        try:
            self._subscribe_k_handles[key].append(handle)
        except KeyError:
            self._subscribe_k_handles[key] = [handle]
    
    def publish(self, key, data) -> None:
        handles = self._subscribe_k_handles.get(key, [])
        for h in handles:
            try:
                h(data)
            except Exception as e:
                print(e)

class ImageState:

    def __init__(self) -> None:
        self.current_image = None
        self.current_image_md5 = None
        self.current_image_path = None
        
        self.count_sift_handle = None