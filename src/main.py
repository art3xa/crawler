import argparse
import crawler

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--target", help="Write url of target")
parser.add_argument("-d", "--depth", help="Write depth of search (default 5)")


if __name__ == '__main__':
    args = parser.parse_args()
    if args.depth is None:
        args.depth = 15
    if args.target is None:
        print("Заполните target")
    else:
        crawler.start(args.target, args.depth)
input()