#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals, print_function
import sys
import os

try:
    from setuptools import setup
except ImportError:
    print(
        "You do not have setuptools, and can not install glowpad. The easiest "
        "way to fix this is to install pip by following the instructions at "
        "http://pip.readthedocs.org/en/latest/installing.html",
        file=sys.stderr,
    )
    sys.exit(1)


def read_reqs(path):
    with open(path, "r") as fil:
        return list(fil.readlines())


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
requires = read_reqs("requirements.txt")
setup(
    name="glowpad",
    version="0.0.1",
    description="Notes Program",
    author="Oliver Schmidhauser",
    author_email="oli@glow.li",
    url="http://github.com/Neo-Oli/glowpad",
    py_modules=["glowpad"],
    install_requires=requires,
    entry_points={
        "console_scripts": [
            "glowpad_processor=glowpad:build",
            "glowpad_processor_lint=glowpad:build_lint",
            "glowpad=glowpad:edit",
        ]
    },
)
