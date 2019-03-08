#!/usr/bin/env python

import sys
import json


if __name__ == '__main__':
    with open(sys.argv[1]) as data_file:
        data = json.load(data_file)
    for k in data.keys():
        if not data[k]:
            data[k] = k
    with open(sys.argv[1], 'w') as outfile:
        json.dump(data, outfile, indent=2)
