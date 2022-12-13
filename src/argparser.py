from argparse import ArgumentParser


class ArgParser:
    """ Argument Parser"""

    def __init__(self, args):
        self._parser = ArgumentParser(prog="Web-crawler",
                                      description="Web-crawler")

        self._args = args
        self._add_arguments()

    def _add_arguments(self):
        """
        Add arguments to the parser
        """
        self._parser.add_argument('target', metavar='URL',
                                  help='Write url of target')
        self._parser.add_argument('-d', '--depth', dest='depth', default=3,
                                  type=int,
                                  help='Write depth of search (default 3)')
        self._parser.add_argument('-t', '--threads', dest='threads', default=1,
                                  type=int,
                                  help='Amount of threads for search (default 1)')

    def parse(self):
        """
        Parse arguments
        """
        args = self._parser.parse_args(self._args)
        return args
