#!/usr/bin/env bash
# . /etc/profile.d/python3.bash
python3 - $@ <<PYTHON
# -*- coding: utf-8 -*-
import re
import sys

from pip import main

if __name__ == '__main__':
    sys.argv[0] = 'pip'
    sys.exit(main())
PYTHON
