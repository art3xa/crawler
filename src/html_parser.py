import re

from lxml import html

url_re = re.compile(
    r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")


class WrapperForHTMLParser:
    """
    Wrapper for HTMLParser
    """

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
