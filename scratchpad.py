#!/bin/python
resultTitle = "Result:"
helptext = """
Welcome to your new scratchpad!

It's basically a normal markdown file except it can run code.
Example:

If you have markdown code block, with a language specified, and the magic comment `#run` (or `# run`) as a first line it will execute it with one of the available processors. To execute, simply press `°`. If you also want to lint your code, press `+`.

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
    {resultTitle}
    ```
    1
    ```
## Processors:

The following processors are available:

* python
    Run python code. The code will additionally be formatted with yapf.
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

#### mode

Default: "eval"

With `mode` different behaviour can be specified.

* `eval`:  (default) Code will be run with the corresponding processor
* `print`: The code will be copied straight to result

#### name

This is the Name of the block. You can set this yourself, otherwise it will just count up to the first free name. With it you can get the output of a higher block inside a lower block.

#### frozen

This boolean specifies if the code should run or not. If it is set to `False` the code will not run regardless if it has changed or not and will keep the result. Use this to make sure a result block doesn't get deleted if the code can no longer run due to some external constraints.

* `true`: The code will not run again
* `false`: The code will execute as normal

###### Getting the output of a previous code block:

You can get the output of a previous (higher) block by reading out the variable scratchpad["<NAME>"].

See also: depends

Example:
    ```python
    #run:{{"name":"firstBlock"}}
    print(1)
    ```

    ```python
    import os
    print(scratchpad["firstBlock"])
    ```
Will turn into:

    ```python
    #run:{{"name":"firstBlock","hash":"1167001081"}}
    print(1)
    ```
    {resultTitle}
    ```
    1
    ```

    ```python
    #run:{{"name":2,"hash":"1202068730"}}
    import os

    print(scratchpad["firstBlock"])
    ```
    ```
    {resultTitle}
    1

    ```

Does not work with gcc or qalc.

#### depends

List of block names.

The block will also run if any of the blocks in depends are updated.


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

#### result_format

Default: ""

Format of the result block. It will add this string to the block opening

Example:
    ```bash
    #run:{{"result_format":"json"}}
    echo '{{"foo":"bar"}}'
    ```
    {resultTitle}
    ```json
    {{"foo":"bar"}}
    ```


""".format(resultTitle=resultTitle)

import os
import sys
import datetime
import sh
import argparse
import fileinput
import tempfile
import random
import json
import glob
import string
import zlib
from base64 import a85encode, a85decode, b64encode
from yapf.yapflib.yapf_api import FormatCode

sh = sh.bake(_return_cmd=True)
os.chdir(os.path.expanduser("~/notes"))
parser = argparse.ArgumentParser()
parser.add_argument("file", help="file to show", nargs="?", default="main")
options = parser.parse_args()
segmentor = "```"
noresult = "NO RESULT\n"
results = {}
scratchpad = {}
configpath = os.path.expanduser("~/.config/scratchpad/")


def hash(language, args, code, result):
    invalidator = 3  # increase this by one to invalidate all hashes
    pastresults = []
    hashargs = ""
    for key in ["name", "always", "echo", "mode"]:
        if key in args:
            hashargs += key + str(args[key])
    if "depends" in args:
        for name in results:
            if name in args["depends"]:
                pastresults.append(results[name])

    hashdata = "".join([
        str(invalidator),
        str(language),
        str(hashargs),
        "code",
        str(code),
        "result",
        str(result),
        "".join(pastresults),
    ])
    # print("###{}@@@".format(hashdata))
    return str(zlib.adler32(bytes(
        hashdata,
        "utf-8",
    )))


def createJson(args):
    return json.dumps(args, separators=(",", ":"))


def name(num):
    return "B{}".format(str(num))


def build_lint():
    build(True)


def build(lint=False):
    output = ""
    data = "\n"
    for line in fileinput.input():
        data += line
    data = data.split("\n" + segmentor)
    data[0] = data[0][1:]
    nextBlockIsResult = False
    for id, val in enumerate(data):
        if nextBlockIsResult:
            nextBlockIsResult = False
            continue
        if val.strip() == resultTitle:
            nextBlockIsResult = True
        elif id % 2 == 0:
            output += val
        else:
            parts = val.split("\n")
            try:
                language = parts.pop(0)
                firstline = parts.pop(0)
            except IndexError:
                language = ""
                firstline = ""
            bang = firstline.split(":")[0]
            if language and bang in ["#run", "# run"]:
                code = "\n".join(parts) + "\n"
                result = noresult
                try:
                    args = json.loads(firstline[firstline.find(":") + 1:])
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
                if "frozen" in args:
                    frozen = args["frozen"]
                else:
                    frozen = False
                try:
                    lastresult = ""
                    if not "result" in args:
                        if data[id + 1].strip() == resultTitle:
                            lastresult = data[id + 2] + "\n"
                    else:
                        lastresult = zlib.decompress(a85decode(
                            args["result"])).decode()
                    lastresult = lastresult.split("\n")
                    try:
                        lastchecksum = args["hash"]
                    except KeyError:
                        lastchecksum = ""
                    lastresultstr = "\n".join(lastresult[1:])
                    if frozen or (lastchecksum == hash(language, args, code,
                                                       lastresultstr)
                                  and not always):
                        result = lastresultstr
                except IndexError:
                    result = noresult
                except zlib.error:
                    result = noresult
                if "linted" in args and not args[
                        "linted"] and lint and not frozen:
                    result = noresult
                if result == noresult:
                    mode = "eval"
                    if "mode" in args:
                        mode = args["mode"]
                    if mode == "eval":
                        lineNumPrepend = output.count("\n") + 3
                        processors = {
                            "php": lambda: php(code, lineNumPrepend, lint),
                            "python":
                            lambda: python(code, lineNumPrepend, lint),
                            "qalc": lambda: qalc(code, lineNumPrepend, lint),
                            "bash": lambda: bash(code, lineNumPrepend, lint),
                            "node": lambda: node(code, lineNumPrepend, lint),
                            "javascript":
                            lambda: node(code, lineNumPrepend, lint),
                            "help": lambda: help(code, lineNumPrepend, lint),
                            "c": lambda: gcc(code, lineNumPrepend, lint),
                        }
                        if language not in processors:
                            result = "No such processor\n"
                        else:
                            now = datetime.datetime.now()
                            code, result, exitcode = processors[language]()
                            args["runtime"] = str(datetime.datetime.now() -
                                                  now)
                            args["exec_date"] = now.replace(
                                microsecond=0).isoformat()
                            if not lint:
                                args["linted"] = lint
                            elif "linted" in args:
                                del args["linted"]
                            args["exitcode"] = exitcode
                            try:
                                if str(result)[-1] != "\n":
                                    result += "%\n"
                            except:
                                pass
                    elif mode == "print":
                        result = code
                    else:
                        result = "Invalid mode\n"
                if not frozen:
                    args["hash"] = hash(language, args, code, result)
                args["frozen"] = frozen
                if "exitcode" in args and not args["exitcode"]:
                    del args["exitcode"]
                if "result" in args and echo:
                    del args["result"]
                resultString = "".join([
                    "\n",
                    str(result),
                ])
                if not echo:
                    args["result"] = a85encode(
                        zlib.compress(
                            "".join(resultString).encode())).decode()
                output += ("\n" + segmentor + language + "\n" + bang + ":" +
                           createJson(args) + "\n" + str(code) + segmentor)
                if echo or ("exitcode" in args and args["exitcode"]):
                    output += ("\n" + resultTitle + "\n" + segmentor +
                               (args["result_format"] if "result_format"
                                in args else "") + resultString + segmentor)
                results[args["name"]] = args["hash"]
                scratchpad[args["name"]] = resultString
            else:
                output += "\n" + segmentor + val + "\n" + segmentor
    print(output, end="")
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
    sh.git("pull")
    editor = "vim"
    if os.environ["EDITOR"] == "nvim":
        editor = "nvim"
    if glob.glob(f"{options.file}*"):
        star = "*"
    else:
        star = ""

    os.system(f'{editor} \
                -c \'nnoremap + :let pos=getpos(".")<CR>:%! scratchpad_processor_lint<CR>:call setpos(".", pos)<CR>zo<CR>\'\
                -c \'nnoremap ° :let pos=getpos(".")<CR>:%! scratchpad_processor<CR>:call setpos(".", pos)<CR>zo<CR>\'\
                {options.file}{star}')
    sh.git("add", "--all")
    st = datetime.datetime.now()
    try:
        sh.git("commit", "-m", "Update on {}".format(st))
    except sh.ErrorReturnCode:
        pass
    sh.git("push")


def prependLineNumbers(code, lineNumPrepend):
    return "\n" * (lineNumPrepend - 1) + str(code)


def php(code, lineNumPrepend, lint=True):
    if lint:
        try:

            newcode = sh.yarn(
                "-s",
                "prettier",
                "--stdin-filepath=foo.php",
                _in=code,
                _err="/dev/null",
                _cwd=os.path.join(sys.prefix, "share/scratchpad-data"),
            )
        except:
            newcode = code
    else:
        newcode = code
    runcode = '<?php $scratchpad=json_decode(base64_decode("{}"), true);{}'.format(
        b64encode(json.dumps(scratchpad).encode("UTF-8")).decode(),
        prependLineNumbers("?>{}".format(newcode), lineNumPrepend),
    )
    data = sh.php(
        _in=runcode,
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    return newcode, str(data), data.exit_code


def python(code, lineNumPrepend, lint=True):
    if lint:
        try:
            newcode = code
            newcode = sh.black("-", "-q", _in=code, _err="/dev/null")
            newcode, changed = FormatCode(
                str(newcode),
                style_config=os.path.join(configpath, ".style.yapf"),
            )
        except:
            newcode = code
    else:
        newcode = code
    runcode = "scratchpad=__import__('json').loads(__import__('base64').b64decode({}))\n{}".format(
        b64encode(json.dumps(scratchpad).encode("UTF-8")),
        prependLineNumbers(newcode, lineNumPrepend),
    )
    data = sh.python(
        _in=runcode,
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    if data.exit_code:
        newcode = code
    return newcode, str(data), data.exit_code


def qalc(code, lineNumPrependm, lint=True):
    data = sh.qalc("--color=no",
                   _in=code,
                   _err_to_out=True,
                   _ok_code=list(range(0, 256)))
    return code, "\n".join(data.split("\n")[:-2]) + "\n", data.exit_code


def bash(code, lineNumPrepend, lint=True):
    if lint:
        try:
            newcode = sh.yarn(
                "-s",
                "prettier",
                "--stdin-filepath=foo.sh",
                _in=code,
                _err="/dev/null",
                _cwd=configpath,
            )
        except:
            newcode = code
    else:
        newcode = code

    runcode = 'declare -A "$(echo "{}" | base64 -d |jq  \'to_entries | map("[\(.key)]=\(.value|@sh)") | reduce .[] as $item ("scratchpad=("; . + ($item) + " ") + ")"\' -r)"\n{}'.format(
        b64encode(json.dumps(scratchpad).encode("UTF-8")).decode(),
        prependLineNumbers(newcode, lineNumPrepend),
    )
    data = sh.bash(
        _in=runcode,
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    if data.exit_code:
        newcode = code
    return newcode, str(data), data.exit_code


def node(code, lineNumPrepend, lint=True):
    if lint:
        try:
            newcode = sh.yarn(
                "-s",
                "prettier",
                "--stdin-filepath=foo.js",
                _in=code,
                _err="/dev/null",
                _cwd=configpath,
            )
        except:
            newcode = code
    else:
        newcode = code

    runcode = (
        "scratchpad=JSON.parse(Buffer.from(\"{}\",'base64').toString());\n{}".
        format(
            b64encode(json.dumps(scratchpad).encode("UTF-8")).decode(),
            prependLineNumbers(newcode, lineNumPrepend),
        ))
    os.environ["NODE_DISABLE_COLORS"] = str(1)
    os.environ["NODE_PATH"] = os.path.join(configpath, "node_modules")

    data = sh.node(
        _in=runcode,
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    if data.exit_code:
        newcode = code
    return newcode, str(data), data.exit_code


def gcc(code, lineNumPrepend, lint=True):
    t = tempfile.mktemp()
    gccout = sh.gcc(
        "-x",
        "c",
        "-",
        "-o",
        t,
        "-fno-color-diagnostics",
        _in=prependLineNumbers(code, lineNumPrepend),
        _err_to_out=True,
        _ok_code=list(range(0, 256)),
    )
    if gccout.exit_code or not os.path.isfile(t):
        return code, gccout, gccout.exit_code
    data = sh.sh("-c", t, _ok_code=list(range(0, 256)), _err_to_out=True)
    os.unlink(t)
    return code, data, data.exit_code


def help(code, lineNumPrepend, lint=True):
    return code, helptext, 0
