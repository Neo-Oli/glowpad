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
parser.add_argument("file", help="file to show", nargs="?", default="main")
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
            if val[:1] != "\n":
                output.append(val)
            else:
                output.append(val[1:])
        else:
            parts = val.split("\n")
            language = parts.pop(0)

            bang = parts.pop(0)
            if bang.startswith("Result:"):
                continue
            if language and bang in ["#run", "# run"]:
                code = "\n".join(parts)
                checksum = str(adler32(bytes("".join([language, code]), "utf-8")))
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
                    processors = {
                        "php": lambda: php(code),
                        "python": lambda: python(code),
                        "qalc": lambda: qalc(code),
                        "bash": lambda: bash(code),
                        "node": lambda: node(code),
                        "javascript": lambda: node(code),
                        "c": lambda: gcc(code),
                    }
                    if language not in processors:
                        result = "No such processor\n"
                    else:
                        code, result = processors[language]()
                output.append(
                    [
                        segmentor,
                        language,
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
                output.append([segmentor, val, segmentor, "\n"])
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
        + "*"
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
    data = sh.php(_in=data, _err_to_out=True, _ok_code=list(range(0, 256)))
    return code, data


def python(code):
    try:
        newcode = sh.black("-", "-q", _in=code, _err="/dev/null")
    except:
        newcode = code
    data = sh.python(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    return newcode, data


def qalc(code):
    data = sh.qalc(
        "--color=no", _in=code, _err_to_out=True, _ok_code=list(range(0, 256))
    )
    data = "\n".join(data.split("\n")[:-2])
    return code, data + "\n"


def bash(code):
    try:
        newcode = sh.yarn("-s",
            "prettier",
            "--stdin-filepath=foo.sh",
            _in=code,
            _err="/dev/null",
            _cwd=os.path.join(sys.prefix,"share/scratchpad-data"),
        )
    except:
        newcode = code
    data = sh.bash(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    return newcode, data


def node(code):
    try:
        newcode = sh.yarn("-s",
            "prettier",
            "--stdin-filepath=foo.js",
            _in=code,
            _err="/dev/null",
            _cwd=os.path.join(sys.prefix,"share/scratchpad-data"),
        )
    except:
        newcode = code
    os.environ["NODE_DISABLE_COLORS"] = str(1)
    data = sh.node(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    return newcode, data


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
