import threading

from typing import Any, Callable, List
from PyQt5.QtCore import QThread, pyqtSignal

class ThreadWork(QThread):

    signal = pyqtSignal(object)
    
    def __init__(self, tid=None) -> None:
        super().__init__()
        self.tid = tid
        self.__init()

    def __init(self):
        self._work = None
        self._args = ()
        self._kwargs = {}
        try:
            self.signal.disconnect()
        except TypeError:
            pass

    def set_work(self, work) -> None:
        self._work = work

    def set_parameters(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        result = self._work(*self._args, **self._kwargs)

        return self.signal.emit(result)
    
    def clear(self) -> None:
        self.__init()


class ThreadWorkS:
    
    def __init__(self, thread_count_max) -> None:
        # 最大进程数
        self._thread_count_max = thread_count_max
        # 所有 thread
        self._threads: list[ThreadWork] = []
        # 使用中的
        self._thread_usins: list[ThreadWork] = []

    def available_number(self):
        return self._thread_count_max - len(self._thread_usins)

    def get(self) -> tuple[ThreadWork | None, int]:
        thread = None
        thread_id = -1

        if len(self._threads) > 0:
            for i, t in enumerate(self._threads):
                if t in self._thread_usins:
                    continue
                thread = t
                thread_id = i
                break

        if thread_id < 0 and len(self._threads) < self._thread_count_max:
            self._threads.append(ThreadWork(len(self._threads)))
            thread_id = len(self._threads) - 1
        
        if thread_id >= 0:
            thread = self._threads[thread_id]
            self._thread_usins.append(thread)            

        return (thread, thread_id)
    
    def release(self, thread_id) -> None:
        if thread_id < 0 or thread_id >= self._thread_count_max:
            return
        
        thread: ThreadWork = self._threads[thread_id]
        thread.clear()
        self._thread_usins.remove(thread)


class _WorkCallable:
        
    def __init__(self, handle: Callable) -> None:
        self.handle = handle
        self.result = None

    def run(self, *args, **kwargs) -> Any:
        self.result = self.handle(*args, **kwargs)

        return self.result


class MultipleThreadState:

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._one_call = True

        self._works: List[_WorkCallable] = []
        self._run_works: List[_WorkCallable] = []
        self._done_works: List[_WorkCallable] = []

    def work(self, work: Callable) -> Callable:
        wc = _WorkCallable(work)
        self._works.append(wc)

        def _work(*args, **kwargs) -> Any:
            self._run_works.append(wc)
            result = wc.run(*args, **kwargs)
            self._done_works.append(wc)
            
            return result

        return _work
    
    def results(self) -> List[Any]:
        results = [w.result for w in self._done_works ]

        return results
    
    def is_done(self) -> bool:
        return len(self._works) == len(self._done_works)
    
    def one_call(self) -> bool:
        with self._lock:
            one_call = self._one_call
            if self._one_call:
                self._one_call = False
        
        return one_call
