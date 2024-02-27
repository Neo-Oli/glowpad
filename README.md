# scratchpad

Someone once explained to me what Jupyter is: "A note taking program that can execute code". Not looking into it any further, I made my own program to do that.

It's basically normal markdown files except it can run code.

## Installation

1. Run `pip install .` in this directory.
2. Copy config-example to `~/.config/scratchpad`
3. Run `npm install` inside `~/.config/scratchpad`.
    * This step is only required if you intend to run JavaScript.
4. Create a folder called `~/notes`.
5. Run `git init` in `~/notes`. 
    * The program will automatically pull, commit and push for you.
    * If you don't want your notes to be saved as a git repository you can also skip this step

## Usage

If you have markdown code block, with a language specified, and the magic comment `#run` (or `# run`) as a first line it will execute it with one of the available processors. To execute, simply press `°`. If you also want to lint your code, press `+`.


### Example
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
### Processors:

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

### Arguments

When executing a block for the first time a JSON formated string of arguments will be generated and inserted after the `#run` directive.
Example:
    #run:{{"name":"B7","hash":"590545889"}}

By default it will contain only name and hash but there are others. Some of them are generated when certain conditions are met. Some of them you can set yourself.

#### Argument List

##### mode

Default: "eval"

With `mode` different behaviour can be specified.

* `eval`:  (default) Code will be run with the corresponding processor
* `print`: The code will be copied straight to result

##### name

This is the Name of the block. You can set this yourself, otherwise it will just count up to the first free name. With it you can get the output of a higher block inside a lower block.

##### frozen

This boolean specifies if the code should run or not. If it is set to `False` the code will not run regardless if it has changed or not and will keep the result. Use this to make sure a result block doesn't get deleted if the code can no longer run due to some external constraints.

* `true`: The code will not run again
* `false`: The code will execute as normal

####### Getting the output of a previous code block:

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

##### depends

List of block names.

The block will also run if any of the blocks in depends are updated.


##### hash

In order to cut down on execution time a hashing system is used. If the code has not changed it will not execute again unless it relies on output of another block that was chagned or the `always` Argument is set to `true`.

##### result

Result of the code compressed using zlib.compress and base64.a85encode. Only used when `echo` is set to `false`.

##### exitcode

Show exit code if it isn't 0.

##### exec_date

Shows the date and time of the last execution.

##### echo

Default: true

If set to false, it will not generate a `Result` block, but it will safe the result into the `result` argument (compressed). This is useful if you want to get the output in another block but don't want to see the result here.

##### always

Default: false

If you want to always execute the block, regardless if it has changed or not you can set this to `true`.

##### result_format

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


## Using python or javascript libraries

If you need additional libraries you can install them.

### Javascript

Go to `~/.config/scratchpad` and run `npm add <your library>`,

### Python

Simply install additional python programs using pip. 
