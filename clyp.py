import os
import sys

from clipboard import copy, paste


def do_copy():
    if sys.argv[1:]:
        copy(" ".join(sys.argv[1:]))
        return True
    elif not os.isatty(sys.stdin.fileno()):
        copy(sys.stdin.read())
        return True
    return False


def main():
    is_copied = do_copy()
    is_ttyout = os.isatty(sys.stdout.fileno())
    if not (is_copied and is_ttyout):
        sys.stdout.write(paste())


if __name__ == '__main__':
    main()