import argparse
import crawler

parser = argparse.ArgumentParser(description='Web-crawler.')
parser.add_argument('target', metavar='URL', help='Write url of target')
parser.add_argument('-d', '--depth', dest='depth', default=3, type=int,
                    help='Write depth of search (default 3)')
parser.add_argument('-t', '--threads', dest='threads', default=1, type=int,
                    help='Amount of threads for search (default 1)')

if __name__ == '__main__':
    args = parser.parse_args()
    crawler.start(args.target, int(args.depth), int(args.threads))
    print('Work completed')
