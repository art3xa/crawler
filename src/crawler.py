import asyncio
import os
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional, List
import re
import aiohttp
from lxml import html
from yarl import URL


MAX_DEPTH = 3
PARSED_URLS = set()
VISITED_HOSTS = {}

url_re = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")


@dataclass
class Task:
    tid: int


class WrapperForHTMLParser:
    @staticmethod
    def parse_links(data):
        tree = html.fromstring(data)
        link_list = tree.xpath('//a')
        result = []
        for link in link_list:
            url = str(link.get('href'))
            if re.match(url_re, url) or url[0] == "/":
                result.append(url)

        return result


@dataclass
class FetchTask(Task):
    tid: int
    url: URL
    depth: int
    Downloads: str = r"\CrawlerDownloads\\"

    def parser(self, cur_page_link, data: str) -> List['FetchTask']:
        if self.depth + 1 > MAX_DEPTH:
            return []
        res = []
        clear_no_filter_urls = []
        links_on_cur_page = WrapperForHTMLParser().parse_links(data)
        for link in links_on_cur_page:
            new_url = URL(link)
            if new_url.host is None and new_url.path.startswith('/'):
                clear_no_filter_urls.append(new_url)
                new_url = URL.build(scheme=self.url.scheme, host=self.url.host,
                                    path=new_url.path,
                                    query_string=new_url.query_string)

            if len(VISITED_HOSTS) > 0 and list(VISITED_HOSTS.keys())[0] not in new_url.host:
                continue
            clear_no_filter_urls.append(new_url)
            if new_url.host not in VISITED_HOSTS:
                robots_url = URL.build(scheme=new_url.scheme,
                                       host=new_url.host, path="/robots.txt")
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(str(robots_url))
                rp.read()
                VISITED_HOSTS[self.url.host] = rp

            if new_url in PARSED_URLS or (
                    self.url.host in VISITED_HOSTS and not VISITED_HOSTS[self.url.host].can_fetch("*", str(new_url))):
                continue

            PARSED_URLS.add(new_url)
            res.append(FetchTask(
                tid=self.tid,
                url=new_url,
                depth=self.depth + 1
            ))
        self.save_page(self.url, data, clear_no_filter_urls)
        return res

    def save_page(self, url, data, parsed_urls):
        t = data
        parsed_urls = list(map(str, parsed_urls))
        for i in range(len(parsed_urls)):
            path = ""
            if "http" in parsed_urls[i][0:4] and '.' in parsed_urls[i]:
                path = self.Downloads + URL(parsed_urls[i]).host + URL(parsed_urls[i]).path
                path = path.replace("/", "\\")
                if path[-1] == '\\':
                    path = path[0:-1] + ".html"
            elif "/" == parsed_urls[i][0]:
                path = self.Downloads + URL(url).host + URL(parsed_urls[i]).path
                path = path.replace("/", "\\")
                if path[-1] == '\\':
                    path = path[0:-1] + ".html"
            path = path.replace("//", "/")
            if "&" not in path and "=" not in path:
                t = t.replace(f'"{parsed_urls[i]}"', f'"{path}"')

        path = self.Downloads + url.host + url.path
        path = path.replace("/", "\\")
        if path[-1] == '\\':
            path = path[0:-1] + ".html"
        else:
            path += ".html"

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, "w") as f:
            print(path)
            f.write(t)

    async def perform(self, pool):
        user_agent = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4240.198 Safari/537.36 '
                          'OPR/72.0.3815.465 (Edition Yx GX)',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=user_agent, allow_redirects=True) as resp:
                # print(self.url, resp.status)
                if resp.content_type == 'text/html':
                    data = await resp.text()
                    # self.save_page(self.url, data)
                    list_tasks: List[FetchTask] = \
                        await asyncio.get_running_loop().run_in_executor(
                            None, self.parser, self.url, data
                        )
                    for task in list_tasks:
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


async def async_start(pool, url):
    await pool.queue.put(FetchTask(
        tid=1,
        url=URL(url),
        depth=1))
    pool.start()
    await pool.queue.join()
    await pool.stop()


def start(url, depth, threads_count):
    loop = asyncio.get_event_loop()
    pool = Pool(threads_count)
    global MAX_DEPTH
    MAX_DEPTH = depth
    try:
        loop.run_until_complete(async_start(pool, url))
    except KeyboardInterrupt:
        loop.run_until_complete(pool.stop())
        loop.close()
