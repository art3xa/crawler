import unittest
from crawler import WrapperForHTMLParser
from unittest.mock import patch, mock_open
from crawler import FetchTask

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
        res = parser.parse_links('<a href="https://www.google.com">Google</a><a href="https://vk.com">Vk</a>')
        self.assertEqual(['https://www.google.com', 'https://vk.com'], res)






class TestFileWriter(unittest.TestCase):
    def test_file_writer(self):
        fake_file_path = "fake/file/path"
        content = "Message to write on file to be written"
        with patch('examples.write_on_file.file_writer.open', mock_open()) as mocked_file:
            FetchTask().write(fake_file_path, content)

            # assert if opened file on write mode 'w'
            mocked_file.assert_called_once_with(fake_file_path, 'w')

            # assert if write(content) was called from the file opened
            # in another words, assert if the specific content was written in file
            mocked_file().write.assert_called_once_with(content)
