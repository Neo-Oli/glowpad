#!/bin/python
envPrefix = "scratchpad_"
helptext = """
Welcome to your new scratchpad!

It's basically a normal markdown file except it can run code.
Example:

If you have markdown code block, with a language specified, and the magic comment `#run` (or `# run`) as a first line it will execute it with one of the available processors. To execute, simply press `+`.

## Example
    ```python
    # run
    print(1)
    ```
Will turn into:
    ```python
    # run:{{"name":1,"hash":"2474772752"}}
    print(1)
    ```
    ```
    Result:
    1
    ```
## Processors:

The following processors are available:

* python
    Run python code. The code will additionally be formatted with black.
* php
    Run php code.
* qalc
    Run block with qalc
* bash
    Run bash code. The code will additionally be formated with prettier.
* node
    Run nodejs code. The code will additionally be formated with prettier.
* javascript (alias for node)
    Run nodejs code. The code will additionally be formated with prettier.
* help
    Show this help message.
* c
    Compile it with gcc and execute it.

## Arguments

When executing a block for the first time a JSON formated string of arguments will be generated and inserted after the `#run` directive.
Example:
    #run:{{"name":7,"hash":"590545889"}}

By default it will contain only name and hash but there are others. Some of them are generated when certain conditions are met. Some of them you can set yourself.

### Argument List

#### name

This is the Name of the block. You can set this yourself, otherwise it will just count up to the first free name. With it you can get the output of a higher block inside a lower block.

###### Getting the output of a previous code block:

You can get the output of a previous (higher) block by reading out the environment variable {envPrefix}<NAME>.

Example:
    ```python
    #run:{{"name":"firstBlock"}}
    print(1)
    ```

    ```python
    import os
    print(os.environ["{envPrefix}firstBlock"])
    ```
Will turn into:

    ```python
    #run:{{"name":"firstBlock","hash":"1167001081"}}
    print(1)
    ```
    ```
    Result:
    1
    ```

    ```python
    #run:{{"name":2,"hash":"1202068730"}}
    import os

    print(os.environ["{envPrefix}firstBlock"])
    ```
    ```
    Result:
    1

    ```

#### hash

In order to cut down on execution time a hashing system is used. If the code has not changed it will not execute again unless it relies on output of another block that was chagned or the `always` Argument is set to `true`.

#### result

Result of the code compressed using zlib.compress and base64.a85encode. Only used when `echo` is set to `false`.

#### echo

Default: true

If set to false, it will not generate a `Result` block, but it will safe the result into the `result` argument (compressed). This is useful if you want to get the output in another block but don't want to see the result here.

#### always

Default: false

If you want to always execute the block, regardless if it has changed or not you can set this to `true`.


""".format(
    envPrefix=envPrefix
)

import os
import sys
import datetime
import sh
import argparse
import fileinput
import tempfile
import random
import json
import string
import zlib
from base64 import a85encode, a85decode

os.chdir(os.path.expanduser("~/notes"))
parser = argparse.ArgumentParser()
parser.add_argument("file", help="file to show", nargs="?", default="main")
options = parser.parse_args()
segmentor = "```"
results = {}


def hash(language, args, code, result):
    invalidator = 1  # increase this by one to invalidate all hashes
    pastresults = []
    for key in ["hash", "result"]:
        if key in args:
            del args[key]
    for name in results:
        if "{}{}".format(envPrefix, name) in code:
            pastresults.append(results[name])

    hashdata = "".join(
        [
            str(invalidator),
            str(language),
            str(args),
            str(code),
            str(result),
            "".join(pastresults),
        ]
    )
    # print("###{}@@@".format(hashdata))
    return str(
        zlib.adler32(
            bytes(
                hashdata,
                "utf-8",
            )
        )
    )


def createJson(args):
    return json.dumps(args, separators=(",", ":"))


def build():
    output = []
    data = "\n"
    for line in fileinput.input():
        data += line
    data = data.split("\n" + segmentor)
    for id, val in enumerate(data):
        if id % 2 == 0:
            if val[:1] != "\n":
                output.append(val)
            else:
                output.append(val[1:])
        else:
            parts = val.split("\n")
            language = parts.pop(0)
            firstline = parts.pop(0)
            bang = firstline.split(":")[0]
            if bang == "Result":
                continue
            if language and bang in ["#run", "# run"]:
                code = "\n".join(parts) + "\n"
                result = "NORESULT"
                try:
                    args = json.loads(firstline[firstline.find(":") + 1 :])
                except json.decoder.JSONDecodeError:
                    args = {}
                if not isinstance(args, dict):
                    args = {}
                if not "name" in args or not args["name"]:
                    args["name"] = 1
                    while args["name"] in results:
                        args["name"] += 1
                if "echo" in args:
                    echo = args["echo"]
                else:
                    echo = True
                if "always" in args:
                    always = args["always"]
                else:
                    always = False
                try:
                    if not "result" in args:
                        lastresult = data[id + 2] + "\n"
                    else:
                        lastresult = zlib.decompress(a85decode(args["result"])).decode()
                    lastresult = lastresult.split("\n")
                    if lastresult[1].startswith("Result:"):
                        try:
                            lastchecksum = args["hash"]
                        except KeyError:
                            lastchecksum = ""
                        lastresultstr = "\n".join(lastresult[2:])
                        # lastresultstr = "{}\n".format(lastresultstr)
                        if (
                            lastchecksum == hash(language, args, code, lastresultstr)
                            and not always
                        ):
                            result = lastresultstr
                except IndexError:
                    result = "NORESULT"
                except zlib.error:
                    result = "NORESULT"
                if result == "NORESULT":
                    processors = {
                        "php": lambda: php(code),
                        "python": lambda: python(code),
                        "qalc": lambda: qalc(code),
                        "bash": lambda: bash(code),
                        "node": lambda: node(code),
                        "javascript": lambda: node(code),
                        "help": lambda: help(code),
                        "c": lambda: gcc(code),
                    }
                    if language not in processors:
                        result = "No such processor\n"
                    else:
                        code, result = processors[language]()
                args["hash"] = hash(language, args, code, result)
                resultString = "".join(
                    [
                        "\n",
                        "Result:",
                        "\n",
                        str(result),
                    ]
                )
                if not echo:
                    args["result"] = a85encode(
                        zlib.compress("".join(resultString).encode())
                    ).decode()
                output.append(
                    [
                        "\n",
                        segmentor,
                        language,
                        "\n",
                        bang,
                        ":",
                        createJson(args),
                        "\n",
                        code,
                        segmentor,
                        "\n",
                    ]
                )
                if echo:
                    output.append(
                        [
                            segmentor,
                            resultString,
                            segmentor,
                            "\n",
                        ]
                    )

                results[args["name"]] = args["hash"]
                os.environ["{}{}".format(envPrefix, args["name"])] = str(result)
            else:
                output.append(
                    [
                        "\n",
                        segmentor,
                        val,
                        "\n",
                        segmentor,
                        "\n",
                    ]
                )
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
    if data.exit_code:
        newcode = code
    return newcode, data


def qalc(code):
    data = sh.qalc(
        "--color=no", _in=code, _err_to_out=True, _ok_code=list(range(0, 256))
    )
    data = "\n".join(data.split("\n")[:-2])
    return code, data + "\n"


def bash(code):
    try:
        newcode = sh.yarn(
            "-s",
            "prettier",
            "--stdin-filepath=foo.sh",
            _in=code,
            _err="/dev/null",
            _cwd=os.path.join(sys.prefix, "share/scratchpad-data"),
        )
    except:
        newcode = code
    data = sh.bash(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    if data.exit_code:
        newcode = code
    return newcode, data


def node(code):
    try:
        newcode = sh.yarn(
            "-s",
            "prettier",
            "--stdin-filepath=foo.js",
            _in=code,
            _err="/dev/null",
            _cwd=os.path.join(sys.prefix, "share/scratchpad-data"),
        )
    except:
        newcode = code
    os.environ["NODE_DISABLE_COLORS"] = str(1)
    data = sh.node(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    if data.exit_code:
        newcode = code
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


def help(code):
    return code, helptext
