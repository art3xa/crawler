import unittest
from unittest.mock import patch, mock_open

from yarl import URL

from src.fetch_task import FetchTask
from src.html_parser import WrapperForHTMLParser


class ParserTest(unittest.TestCase):
    def test_single_url(self):
        parser = WrapperForHTMLParser()
        res = parser.parse_links('<a href="https://www.google.com">Google</a>')
        self.assertEqual(['https://www.google.com'], res)

    def test_no_url(self):
        parser = WrapperForHTMLParser()
        res = parser.parse_links('<a>Google</a>')
        self.assertEqual([], res)

    def test_multiple_urls(self):
        parser = WrapperForHTMLParser()
        res = parser.parse_links(
            '<a href="https://www.google.com">Google</a><a href="https://vk.com">Vk</a>')
        self.assertEqual(['https://www.google.com', 'https://vk.com'], res)


class TestFileWriter(unittest.TestCase):
    def test_parser(self):
        with patch('builtins.open', mock_open()) as m:
            task = FetchTask(1, URL('https://www.google.com'), 1)
            task.parser('https://www.google.com',
                        '<a href="https://www.google.com">Google</a>', 2)
            m.assert_called_once_with(
                '\\CrawlerDownloads\\\\www.google.com.html', 'w')

    def test_parser_with_no_url(self):
        with patch('builtins.open', mock_open()) as m:
            task = FetchTask(1, URL('https://www.google.com'), 1)
            task.parser('https://www.google.com', '<a>Google</a>', 2)
            m.assert_called_once_with(
                '\\CrawlerDownloads\\\\www.google.com.html', 'w')

    def test_parser_with_multiple_urls(self):
        with patch('builtins.open', mock_open()) as m:
            task = FetchTask(1, URL('https://www.google.com'), 1)
            task.parser(
                'https://www.google.com',
                '<a href="https://www.google.com">Google</a><a href="https://vk.com">Vk</a>',
                2)
            m.assert_called_once_with(
                '\\CrawlerDownloads\\\\www.google.com.html', 'w')

    @patch('builtins.open', new_callable=mock_open)
    def test_parser_with_multiple_urls_and_no_url(self, mock_file):
        handle = mock_file()
        task = FetchTask(1, URL('https://www.google.com'), 1)
        task.parser(
            'https://www.google.com',
            '<a href="https://www.google.com">Google</a><a href="https://vk.com">Vk</a><a>Google</a>',
            2)
        handle.write.assert_called_once_with(
            '<a href="\\CrawlerDownloads\\\\www.google.com.html">Google</a><a href="https://vk.com">Vk</a><a>Google</a>')

    @patch('builtins.open', new_callable=mock_open)
    def test_parser_with_multiple_urls_and_no_url_and_no_href(self, mock_file):
        handle = mock_file()
        task = FetchTask(1, URL('https://www.google.com'), 1)
        task.parser(
            'https://www.google.com',
            '<a href="https://www.google.com">Google</a><a href="https://vk.com">Vk</a><a>Google</a><a>Google</a>',
            2)
        handle.write.assert_called_once_with(
            '<a href="\\CrawlerDownloads\\\\www.google.com.html">Google</a><a href="https://vk.com">Vk</a><a>Google</a><a>Google</a>')
