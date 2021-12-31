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
    #run:{{"name":"B7","hash":"590545889"}}

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

#### exitcode

Show exit code if it isn't 0.

#### exec_date

Shows the date and time of the last execution.

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
    invalidator = 2  # increase this by one to invalidate all hashes
    pastresults = []
    hashargs = ""
    for key in ["name", "always", "echo"]:
        if key in args:
            hashargs += str(args[key])
    for name in results:
        if "{}{}".format(envPrefix, name) in code:
            pastresults.append(results[name])

    hashdata = "".join(
        [
            str(invalidator),
            str(language),
            str(hashargs),
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


def name(num):
    return "B{}".format(str(num))


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
                    i = 1
                    while name(i) in results:
                        i += 1
                    args["name"] = name(i)
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
                        now=datetime.datetime.now()
                        args["exec_date"]=now.replace(microsecond=0).isoformat()
                        code, result, exitcode = processors[language]()
                        args["exitcode"] = exitcode
                args["hash"] = hash(language, args, code, result)
                if "exitcode" in args and not args["exitcode"]:
                    del args["exitcode"]
                if "result" in args and echo:
                        del args["result"]
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
                if echo or ("exitcode" in args and args["exitcode"]):
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
    out = ""
    for i in output:
        if isinstance(i, str):
            out += str(i)
        else:
            for j in i:
                out += str(j)
    print(out, end="")
    # try:
    # newout = sh.yarn(
    # "-s",
    # "prettier",
    # "--stdin-filepath=foo.md",
    # _in=out,
    # _err="/dev/null",
    # _cwd=os.path.join(sys.prefix, "share/scratchpad-data"),
    # )
    # except:
    # newout = out

    # print(newout, end="")


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
    return code, data, data.exit_code


def python(code):
    try:
        newcode = sh.black("-", "-q", _in=code, _err="/dev/null")
    except:
        newcode = code
    data = sh.python(_in=code, _err_to_out=True, _ok_code=list(range(0, 256)))
    if data.exit_code:
        newcode = code
    return newcode, data, data.exit_code


def qalc(code):
    data = sh.qalc(
        "--color=no", _in=code, _err_to_out=True, _ok_code=list(range(0, 256))
    )
    return code, "\n".join(data.split("\n")[:-2]) + "\n", data.exit_code


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
    return newcode, data, data.exit_code


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
    return newcode, data, data.exit_code


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
    if gccout.exit_code or not os.path.isfile(t):
        return code, gccout, gccout.exit_code
    data = sh.sh("-c", t, _ok_code=list(range(0, 256)), _err_to_out=True)
    os.unlink(t)
    return code, data, data.exit_code


def help(code):
    return code, helptext, 0
