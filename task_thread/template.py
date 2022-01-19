"""NAME.py : Description of the file

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.1

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""

# stdlib
import sys
import logging
import asyncio

def test1():
    st = """Empty test
    """
    pre = __name__ + "test1 :"
    print(pre, st)


def test2():
    st = """Empty test
    """
    pre = __name__ + "test2 :"
    print(pre, st)


def main():
    pre = __name__ + "main :"
    print(pre, "main: arguments: ", sys.argv)
    if (len(sys.argv) < 2):
        print(pre, "main: needs test number")
    else:
        st = "test" + str(sys.argv[1]) + "()"
        exec(st)


if (__name__ == "__main__"):
    main()
