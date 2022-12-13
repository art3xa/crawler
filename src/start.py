import asyncio

from yarl import URL

from src.fetch_task import FetchTask
from src.pool import Pool


async def async_start(pool, url):
    """
    Start async crawling
    :param pool:
    :param url:
    :return:
    """
    await pool.queue.put(FetchTask(
        tid=1,
        url=URL(url),
        depth=1))
    pool.start()
    await pool.queue.join()
    await pool.stop()


def start(url, depth, threads_count):
    """
    Start crawling
    :param url:
    :param depth:
    :param threads_count:
    :return:
    """
    loop = asyncio.get_event_loop()
    pool = Pool(threads_count, max_depth=depth)
    try:
        loop.run_until_complete(async_start(pool, url))
    except KeyboardInterrupt:
        loop.run_until_complete(pool.stop())
        loop.close()
