#!/bin/python
import os
import sys
import datetime
import sh
import argparse
import fileinput
import tempfile
from zlib import adler32

os.chdir(os.path.expanduser("~/notes"))
parser = argparse.ArgumentParser()
parser.add_argument("file", help="file to show", nargs="?", default="main.*")
options = parser.parse_args()
segmentor = "```"


def build():
    output = []
    data = ""
    for line in fileinput.input():
        data += line
    data = data.split(segmentor)
    for id, val in enumerate(data):
        if id % 2 == 0:
            if val != "\n":
                output.append(val.lstrip("\n"))
        else:
            parts = val.split("\n")
            parts.pop(0)
            bang = parts.pop(0)
            bangparts = bang.split(":")
            if bang.startswith("Result:"):
                continue
            if len(bangparts) == 2 and bangparts[0] == "run":
                code = "\n".join(parts)
                checksum = str(adler32(bytes(code, "utf-8")))
                result = "NORESULT"
                try:
                    lastresult = data[id + 2].split("\n")
                    if lastresult[1].startswith("Result:"):
                        lastchecksum = lastresult[1].split(":")[1]
                        if lastchecksum == checksum:
                            result = "\n".join(lastresult[2:])
                except IndexError:
                    pass
                if result == "NORESULT":
                    processor = bangparts[1]
                    processors = {
                        "php": lambda: php(code),
                        "python": lambda: python(code),
                        "qalc": lambda: qalc(code),
                        "bash": lambda: bash(code),
                        "node": lambda: node(code),
                        "gcc": lambda: gcc(code),
                    }
                    if processor not in processors:
                        result = "No such processor\n"
                    else:
                        code, result = processors[processor]()
                output.append(
                    [
                        segmentor,
                        "\n",
                        bang,
                        "\n",
                        code,
                        segmentor,
                        "\n",
                        segmentor,
                        "\n",
                        "Result:{}".format(checksum),
                        "\n",
                        result,
                        segmentor,
                        "\n",
                    ]
                )
            else:
                output.append([separator, val, separator])
    for i in output:
        if isinstance(i, str):
            print(i, end="")
        else:
            for j in i:
                print(j, end="")


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


def php(code):
    data = "<?php {} ?>".format(code)
    data = sh.php(_in=data, _err_to_out=True, _ok_code=list(range(0, 256)), _bg=True)
    return code, data


def python(code):
    try:
        newcode = sh.black("-", "-q", _in=code, _err="/dev/null", bg=True)
    except:
        newcode = code
    data = sh.python(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)), _bg=True)
    return newcode, data


def qalc(code):
    data = sh.qalc(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)), _bg=True)
    data = "\n".join(data.split("\n")[:-2])
    return code, data + "\n"


def bash(code):
    data = sh.bash(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)), _bg=True)
    return code, data


def node(code):
    os.environ["NODE_DISABLE_COLORS"] = str(1)
    data = sh.node(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)), _bg=True)
    return code, data


def gcc(code):
    t = tempfile.mktemp()
    gccout = sh.gcc(
        "-x",
        "c",
        "-",
        "-o",
        t,
        "-fno-color-diagnostics",
        _in=code,
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    if os.path.isfile(t):
        try:
            data = sh.sh("-c", t)
        except:
            data = "Execution failed\n"
        os.unlink(t)
    else:
        data = gccout
    return code, data
