import argparse
import crawler

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--target", help="Write url of target")
parser.add_argument("-d", "--depth", help="Write depth of search (default 3)")
parser.add_argument("-c", "--threads_count", help="Amount of threads for search (default 1)")

if __name__ == '__main__':
    args = parser.parse_args()
    if args.depth is None:
        args.depth = 3
    if args.target is None:
        print("Заполните target")
        exit(-1)
    if args.threads_count is None:
        args.threads_count = 1
    crawler.start(args.target, int(args.depth), int(args.threads_count))
print('Work completed')
