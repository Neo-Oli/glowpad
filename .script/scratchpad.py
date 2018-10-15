#!/bin/python
import os
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
    print("php")
    return data

def prepare():
    output=""
    cachedir=".cache"
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    for f in glob.glob(".cache/*"):
        os.remove(f)
    for f in glob.glob("*"):
        with open(f, 'rb') as file:
            data=file.read()
        parts=f.split(".")
        parts.reverse()
        parts.pop()
        for part in parts:
            processors={
                "gpg": lambda: gpg(data),
                "md": lambda: md(data),
                "php": lambda: php(data),
            }
            data=processors[part]()
        output="{}\n{}".format(output,data)
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
    print(output)
def prepare_gpg():
    # unlocking gpg, because vim-gpg has problems with input
    sh.gpg(sh.gpg("--quiet", "--armor", "-e", "-r", "oli@glow.li", _in="BEAR"), "-d")
