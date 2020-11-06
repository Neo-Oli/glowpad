#!/bin/python
import os
import sys
import datetime
import sh
import argparse
import fileinput

os.chdir(os.path.expanduser("~/notes"))

parser = argparse.ArgumentParser()
parser.add_argument("file", help="file to show", nargs="?", default="main.*")
options = parser.parse_args()


def php(code):
    data = "<?php {} ?>".format(code)
    data = sh.php(_in=data)
    return code, data


def python(code):
    try:
        code = sh.black("-", "-q", _in=code, _err="/dev/null")
    except:
        pass
    data = sh.python(_in=code, _err_to_out=True, _ok_code=[0, 1])
    return code, data


def qalc(code):
    data = sh.qalc(_in=code)
    return code, data


def bash(code):
    data = sh.bash(_in=code)
    return code, data


def build():
    output = ""
    data = ""
    for line in fileinput.input():
        data += line
    for id, val in enumerate(data.split("```")):
        if id % 2 == 0:
            if val != "\n":
                output = "{}{}".format(output, val)
        else:
            parts = val.split("\n")
            parts.pop(0)
            bang = parts.pop(0)
            bangparts = bang.split(":")
            if bang == "Result:":
                continue
            if len(bangparts) == 2 and bangparts[0] == "run":
                processor = bangparts[1]
                code = "\n".join(parts)
                processors = {
                    "php": lambda: php(code),
                    "python": lambda: python(code),
                    "qalc": lambda: qalc(code),
                    "bash": lambda: bash(code),
                }
                code, result = processors[processor]()
                output = "{}```\n{}\n{}```\n```\nResult:\n{}```".format(
                    output, bang, code, result
                )
            else:
                output = "{}```{}```".format(output, val)
    print(output, end="")


def edit():
    os.system(
        "nvim -c 'set nolist' -c 'nnoremap + "
        + ':let pos=getpos(".")<CR>'
        + ":%! scratchpad_processor<CR>"
        + ':call setpos(".", pos)<CR>'
        + "' "
        + options.file
    )
    sh.git("add", "--all")
    st = datetime.datetime.now()
    try:
        sh.git("commit", "-m", "Update on {}".format(st))
    except sh.ErrorReturnCode:
        pass
    sh.git("push")
