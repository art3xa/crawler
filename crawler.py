import sys

from src.argparser import ArgParser
from src.start import start


def get_args():
    """ Get arguments from command line """
    arg_parser = ArgParser(sys.argv[1:])
    try:
        args = arg_parser.parse()
    except ValueError as e:
        print(str(e))
        sys.exit()
    return args


if __name__ == '__main__':
    try:
        args = get_args()
        start(args.target, int(args.depth), int(args.threads))
        print('Work completed')
    except KeyboardInterrupt:
        print('Work interrupted')
        exit(0)
