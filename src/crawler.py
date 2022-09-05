import asyncio
from dataclasses import dataclass
from typing import Optional, List
import bs4
from yarl import URL
import aiohttp
import lxml


MAX_DEPTH = 10
PARSED_URLS = set()


@dataclass
class Task:
    tid: int


@dataclass
class FetchTask(Task):
    tid: int
    url: URL
    depth: int

    def parser(self, data: str) -> List['FetchTask']:
        if self.depth + 1 > MAX_DEPTH:
            return []
        soup = bs4.BeautifulSoup(data, 'lxml')
        res = []
        for link in soup.find_all('a', href=True):
            new_url = URL(link['href'])
            if new_url.host is None and new_url.path.startswith('/'):
                new_url = URL.build(
                    scheme=self.url.scheme,
                    host=self.url.host,
                    path=new_url.path,
                    query_string=new_url.query_string
                )
                if new_url in PARSED_URLS:
                    continue
                PARSED_URLS.add(new_url)
                res.append(FetchTask(
                    tid=self.tid,
                    url=new_url,
                    depth=self.depth + 1
                ))
        return res

    async def perform(self, pool):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as resp:
                print(self.url, resp.status)
                data = await resp.text()
                res: List[FetchTask] = \
                    await asyncio.get_running_loop().run_in_executor(
                    None, self.parser, data
                )
                for task in res:
                    await pool.queue.put(task)


class Pool:
    def __init__(self, max_rate: int, interval: int = 1,
                 concurrent_level: Optional[int] = None):
        self.max_rate = max_rate
        self.interval = interval
        self.concurrent_level = concurrent_level
        self.is_running = False
        self.queue = asyncio.Queue()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(concurrent_level or max_rate)
        self._concurrent_workers = 0
        self._stop_event = asyncio.Event()

    async def _scheduler(self):
        while self.is_running:
            for _ in range(self.max_rate):
                async with self._semaphore:
                    task = await self.queue.get()
                    asyncio.create_task(self._worker(task))
            await asyncio.sleep(self.interval)

    def start(self):
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler())

    async def _worker(self, task: FetchTask):
        async with self._semaphore:
            self._concurrent_workers += 1
            await task.perform(self)
            self.queue.task_done()
        self._concurrent_workers -= 1
        if not self.is_running and self._concurrent_workers == 0:
            self._stop_event.set()

    async def stop(self):
        self.is_running = False
        self._scheduler_task.cancel()
        if self._concurrent_workers != 0:
            await self._stop_event.wait()


async def start(pool):
    await pool.queue.put(FetchTask(
        tid=1,
        url=URL('https://habr.com/ru/hub/python/'),
        depth=1))
    pool.start()
    await pool.queue.join()
    await pool.stop()


def main():
    loop = asyncio.get_event_loop()
    pool = Pool(3)
    try:
        loop.run_until_complete(start(pool))
    except KeyboardInterrupt:
        loop.run_until_complete(pool.stop())
        loop.close()


if __name__ == '__main__':
    main()
