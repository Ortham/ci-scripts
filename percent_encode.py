#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import urllib.parse

if __name__ == "__main__":
    if len(sys.argv) == 2:
        input = sys.argv[1]
    else:
        input = sys.stdin.read().strip()

    output = urllib.parse.quote(input, safe='')
    print(output)
