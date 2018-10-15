#!/bin/python
import os
import sys
import datetime
import sh
import glob
def gpg(data):
    data=sh.gpg("-d", _in=data)
    return data

def md(data):
    data=sh.msee(_in=data)
    return data

def php(data):
    data="<?php {} ?>".format(data)
    data=sh.php(_in=data)
    return data
def python(data):
    data=sh.python(_in=data)
    return data

def bash(data):
    data=sh.bash(_in=data)
    return data

def prepare():
    output=""
    cachedir=".cache"
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    for f in glob.glob(".cache/*"):
        os.remove(f)
    for f in sorted(glob.glob("*")):
        with open(f, 'rb') as file:
            data=file.read()
        data=gpg(data)
        parts=data.split("```")
        data=""
        for id, val in enumerate(parts):
            if id % 2 == 0:
                data="{}{}".format(data,val)
            else:
                parts=val.split("\n")
                parts.pop(0)
                bang=parts.pop(0)
                bangparts=bang.split(":")
                if len(bangparts) == 2 and bangparts[0] == "run":
                    processor=bangparts[1]
                    code="\n".join(parts)
                    processors={
                        "php": lambda: php(code),
                        "python": lambda: python(code),
                        "bash": lambda: bash(code),
                    }
                    result=processors[processor]()
                    data="{}\nrun {}:\n```{}\n{}\n```\nResult:\n```\n{}\n```".format(data,processor,processor,code,result)
                else:
                    data="{}\n```\n{}\n```".format(data,val)

        output="{}\n{}".format(output,data)
    output=md(output)
    enc=sh.gpg("--batch","--armor", "--quiet", "-e", "-r", "oli@glow.li",_in=output)
    enc=str(enc)
    with open("{}/{}".format(cachedir,"output"), 'w') as file:
        file.write(enc)
    return output
def edit():
    os.chdir(os.path.expanduser("~/notes"))
    prepare_gpg()
    os.system("nvim *")
    prepare()
    sh.git("add", glob.glob("*"))
    st = datetime.datetime.now()
    try:
        sh.git("commit", "-m", "Update on {}".format(st))
    except sh.ErrorReturnCode:
        pass
    sh.git("push")
def show():
    os.chdir(os.path.expanduser("~/notes"))
    prepare_gpg()
    if not os.path.isfile(".cache/output"):
        output=prepare()
    else:
        output=str(sh.gpg("--batch","--quiet", "-d", ".cache/output"))
    sh.less("-RS",_out=sys.stdout,_in=output,_err=sys.stderr)
def debug():
    os.chdir(os.path.expanduser("~/notes"))
    prepare_gpg()
    print(prepare())
def prepare_gpg():
    # unlocking gpg, because vim-gpg has problems with input
    sh.gpg(sh.gpg("--quiet", "--armor", "-e", "-r", "oli@glow.li", _in="BEAR"), "-d")
