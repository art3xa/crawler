import asyncio
import os
import threading
import urllib.robotparser
from dataclasses import dataclass
from typing import List

import aiohttp
from yarl import URL

from src.html_parser import WrapperForHTMLParser

PARSED_URLS = set()
VISITED_HOSTS = {}
lock = threading.Lock()


@dataclass
class Task:
    """
    This class is used to store all the task arguments
    """
    tid: int


@dataclass
class FetchTask(Task):
    tid: int
    url: URL
    depth: int
    Downloads: str = r"\CrawlerDownloads\\"

    def parser(self, cur_page_link, data: str, MAX_DEPTH: int) -> List[
        'FetchTask']:
        """
        Парсит html страницу
        :param cur_page_link:
        :param data:
        :param MAX_DEPTH:
        :return:
        """
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

            if len(VISITED_HOSTS) > 0 and list(
                    VISITED_HOSTS.keys())[0] not in new_url.host:
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

    def format_path(self, url: URL, data: str, parsed_urls):
        """
        Форматирует путь для сохранения html страницы
        :param url:
        :param data:
        :param parsed_urls:
        :return:
        """
        temp = data
        for i in range(len(parsed_urls)):
            path = ""
            if "http" in parsed_urls[i][0:4] and '.' in parsed_urls[i]:
                path = self.Downloads + \
                       URL(parsed_urls[i]).host + URL(parsed_urls[i]).path
                path = path.replace("/", "\\")
                if path[-1] == '\\':
                    path = path[0:-1] + ".html"
            elif "/" == parsed_urls[i][0]:
                path = self.Downloads + \
                    URL(url).host + URL(parsed_urls[i]).path
                path = path.replace("/", "\\")
                if path[-1] == '\\':
                    path = path[0:-1] + ".html"
            path = path.replace("//", "/")
            if "&" not in path and "=" not in path:
                temp = temp.replace(f'"{parsed_urls[i]}"', f'"{path}"')
        return temp

    def save_page(self, url: URL, data: str, parsed_urls: List[URL]):
        """
        Сохраняет html страницу
        :param url: URL
        :param data: html страница
        :param parsed_urls: список ссылок на странице
        """
        parsed_urls = list(map(str, parsed_urls))
        temp = self.format_path(url, data, parsed_urls)
        path = self.format_path_html(url)
        print(path)
        self.save(path, temp)

    def format_path_html(self, url: URL) -> str:
        """
        Форматирует путь для сохранения html страницы
        :param url: URL
        :return:
        """
        path = self.Downloads + url.host + url.path
        path = path.replace("/", "\\")
        if path[-1] == '\\':
            path = path[0:-1] + ".html"
        else:
            path += ".html"
        return path

    @staticmethod
    def save(path: str, temp: str) -> None:
        """
        Сохраняет html страницу в файл
        :param path:
        :param temp:
        :return:
        """
        lock.acquire()
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, "w") as f:
            f.write(temp)
        lock.release()

    async def perform(self, pool):
        """
        Выполняет задачу
        :param pool:
        :return:
        """
        user_agent = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4240.198 Safari/537.36 '
                          'OPR/72.0.3815.465 (Edition Yx GX)',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=user_agent,
                                   allow_redirects=True) as resp:
                if resp.content_type == 'text/html':
                    data = await resp.text()
                    list_tasks: List[FetchTask] = \
                        await asyncio.get_running_loop().run_in_executor(
                            None, self.parser, self.url, data, pool.max_depth
                        )
                    for task in list_tasks:
                        await pool.queue.put(task)
