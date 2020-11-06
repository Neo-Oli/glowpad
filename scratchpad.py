#!/bin/python
import os
import sys
import datetime
import sh
import glob
import argparse

os.chdir(os.path.expanduser("~/notes"))
cachedir = ".cache"

parser = argparse.ArgumentParser()
parser.add_argument("file", help="file to show", nargs="?", default="main")
options = parser.parse_args()


def gpg(data):
    data = sh.gpg("-d", _in=data)
    return data


def md(data):
    data = sh.msee(_in=data)
    return data


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


def build(f):
    cache = "{}/{}".format(cachedir, f)
    with open(f, "rb") as file:
        data = file.read()
    data = gpg(data)
    output = ""
    if not os.path.exists(cache) or os.path.getmtime(f) > os.path.getmtime(cache):
        parts = data.split("```")
        for id, val in enumerate(parts):
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
        enc = sh.gpg(
            "--batch", "--armor", "--quiet", "-e", "-r", "oli@glow.li", _in=output
        )
        enc = str(enc)
        with open(f, "w") as file:
            file.write(enc)
        with open(cache, "w") as file:
            file.write("")
        return str(output)
    else:
        return str(data)


def edit():
    prepare_gpg()
    os.system("nvim -c 'set nolist' -c 'nnoremap + :w<CR>:!S<CR>:e<CR>' main.*")
    update()
    sh.git("add", "--all")
    st = datetime.datetime.now()
    try:
        sh.git("commit", "-m", "Update on {}".format(st))
    except sh.ErrorReturnCode:
        pass
    sh.git("push")


def update():
    prepare_gpg()
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    for f in glob.glob("{}/*".format(cachedir)):
        basename = os.path.basename(f)
        if not os.path.exists(basename):
            os.remove(f)
    output = {}
    files = glob.glob("**/*.build*", recursive=True)
    files.sort()
    for f in files:
        name = f.split(".")[0]
        output[name] = build(f)
    buildname = os.path.basename(options.file).split(".")[0]
    scratchpad = output[buildname]
    old = ""
    while old != scratchpad:
        old = scratchpad
        for f in files:
            name = f.split(".")[0]
            replace = "[[{}]]".format(name)
            scratchpad = scratchpad.replace(replace, output[name])
    return scratchpad


def rebuild():
    update()


def show():
    output = update()
    print(output)
    # sh.less("-RSF",_out=sys.stdout,_in=output,_err=sys.stderr)


def prepare_gpg():
    # unlocking gpg, because vim-gpg has problems with input
    sh.gpg(sh.gpg("--quiet", "--armor", "-e", "-r", "oli@glow.li", _in="BEAR"), "-d")
