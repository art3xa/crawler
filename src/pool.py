import asyncio
from typing import Optional


class Pool:
    def __init__(self, max_rate: int, interval: int = 1,
                 concurrent_level: Optional[int] = None, max_depth: int = 3):

        self.max_rate = max_rate
        self.interval = interval
        self.concurrent_level = concurrent_level
        self.is_running = False
        self.queue = asyncio.Queue()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(concurrent_level or max_rate)
        self._concurrent_workers = 0
        self._stop_event = asyncio.Event()
        self.max_depth = max_depth

    async def _scheduler(self):
        """
        Запускает задачи в пуле
        :return:
        """
        while self.is_running:
            for _ in range(self.max_rate):
                async with self._semaphore:
                    task = await self.queue.get()
                    asyncio.create_task(self._worker(task))
            await asyncio.sleep(self.interval)

    def start(self):
        """
        Запускает пул
        :return:
        """
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler())

    async def _worker(self, task):
        """
        Выполняет задачу
        :param task:
        :return:
        """
        async with self._semaphore:
            self._concurrent_workers += 1
            await task.perform(self)
            self.queue.task_done()
        self._concurrent_workers -= 1
        if not self.is_running and self._concurrent_workers == 0:
            self._stop_event.set()

    async def stop(self):
        """
        Останавливает пул
        :return:
        """
        self.is_running = False
        self._scheduler_task.cancel()
        if self._concurrent_workers != 0:
            await self._stop_event.wait()
