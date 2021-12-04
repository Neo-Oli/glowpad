#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals, print_function
import sys
import os


try:
    from setuptools import setup
except ImportError:
    print(
        "You do not have setuptools, and can not install scratchpad. The easiest "
        "way to fix this is to install pip by following the instructions at "
        "http://pip.readthedocs.org/en/latest/installing.html\n"
        "Alternately, you can run pet  without installing it by running "
        '"python pet .py"',
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
    name="scratchpad",
    version="0.0.0",
    description="Notes Program",
    author="Oliver Schmidhauser",
    author_email="oli@glow.li",
    # url='http://github.com/Neo-Oli/pet',
    py_modules=["scratchpad"],
    # include_package_data=True,
    # license='',
    # platforms='Linux x86, x86-64',
     data_files=[('share/scratchpad-data', ['package.json', 'yarn.lock',".prettierrc.json"]),]
,    install_requires=requires,
    entry_points={
        "console_scripts": [
            "scratchpad_processor=scratchpad:build",
            "s=scratchpad:edit",
        ]
    },
)
