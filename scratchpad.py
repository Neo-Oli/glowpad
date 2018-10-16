#!/bin/python
import os
import sys
import datetime
import sh
import glob
os.chdir(os.path.expanduser("~/notes"))
cachedir=".cache"
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

def build(f,bare=False):
    cache="{}/{}".format(cachedir,f)
    if not os.path.exists(cache) or os.path.getmtime(f) > os.path.getmtime(cache) or bare:
        with open(f, 'rb') as file:
            data=file.read()
        data=gpg(data)
        parts=data.split("```")
        data=""
        output=""
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
                    data="{}\n```{}\n#!/usr/bin/env {}\n{}\n```\nResult:\n```\n{}```".format(data,processor,processor,code,result)
                else:
                    data="{}\n```\n{}\n```".format(data,val)
        output="{}\n{}".format(output,data)
        if bare:
            return output
        output=md(output)
        enc=sh.gpg("--batch","--armor", "--quiet", "-e", "-r", "oli@glow.li",_in=output)
        enc=str(enc)
        with open(cache, 'w') as file:
            file.write(enc)
    else:
        output=str(sh.gpg("--batch","--quiet", "-d", cache))
    return str(output)
def edit():
    prepare_gpg()
    os.system("nvim *")
    update()
    sh.git("add", "--all")
    st = datetime.datetime.now()
    try:
        sh.git("commit", "-m", "Update on {}".format(st))
    except sh.ErrorReturnCode:
        pass
    sh.git("push")

def update(bare=False):
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    for f in glob.glob("{}/*".format(cachedir)):
        basename=os.path.basename(f)
        if not os.path.exists(basename):
            os.remove(f)
    output=""
    for f in sorted(glob.glob("*")):
        output+=build(f,bare)
    return output

def show():
    prepare_gpg()
    output=update();
    sh.less("-RSF",_out=sys.stdout,_in=output,_err=sys.stderr)
def bare():
    prepare_gpg()
    output=update(bare);
    print(output)
def prepare_gpg():
    # unlocking gpg, because vim-gpg has problems with input
    sh.gpg(sh.gpg("--quiet", "--armor", "-e", "-r", "oli@glow.li", _in="BEAR"), "-d")
