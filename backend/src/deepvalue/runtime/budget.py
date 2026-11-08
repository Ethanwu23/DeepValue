import threading
import time
from deepvalue.contracts.common import CapabilityError


class Budget:
    """同一运行的所有线程共享计数与取消信号。"""
    def __init__(self, *, requests=80, models=8, seconds=600, clock=time.monotonic):
        if requests < 1 or models < 1 or seconds <= 5:
            raise ValueError("预算必须为正，且预留五秒整理结果")
        self.limit, self.model_limit = requests, models
        self.clock = clock
        self.deadline = clock() + seconds - 5
        self.requests = self.models = 0
        self.cancelled = False
        self.lock = threading.Lock()

    def reserve(self, *, model=False):
        with self.lock:
            if self.cancelled:
                raise CapabilityError("CANCELLED", "runtime", "研究已取消")
            if self.clock() >= self.deadline:
                raise CapabilityError("DEADLINE_EXCEEDED", "runtime", "外部请求截止时间已到")
            if self.requests >= self.limit or (model and self.models >= self.model_limit):
                raise CapabilityError("BUDGET_EXHAUSTED", "runtime", "调用预算已耗尽")
            self.requests += 1
            self.models += int(model)

    def remaining(self):
        return max(0, self.deadline - self.clock())

    def cancel(self):
        with self.lock:
            self.cancelled = True
