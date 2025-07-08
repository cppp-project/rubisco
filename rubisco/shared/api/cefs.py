# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the Rubisco.
#
# Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Rubisco extension API for Rubisco Comand Event Filesystem.

The CEFS is too complex. Although it is a part of Rubisco kernel. but I will put
it into `rubisco.shared.api.cefs`.

```text
User Control Interface <---> CEFS <---> Event defined by extension, cli, etc.
```

CEFS like a filesystem, but it is not a real filesystem that can store files.
CEFS is a router system that connect user's command and developers' event.

CEFS supports file, directory, symlink(alias), and mount point. Each event
object has "stat" that contains its metadata, such as type, options, and other
attributes.

File:
The "file" is the real event executor, Every executable command must be routed
to a file. File supports "arguments" and "file data".

Directory:
The "directory" is collection of event objects, directory supports "options".

Symlink:
The "symlink"/"alias" is alias of an event object, it can be used to create a
shortcut to another event object.

Mount point:
The "mount point" is a special directory that can "mount" external commands from
system shell. It is not implemented yet.

Example:
This is a simple CEFS tree structure:

```text
/ (root)
├── file1
├── file2
├── dir1
│   ├── file3
│   └── symlink1 -> "/file1"
└── mount1 -> "sudo apt"
```

In CLI's we can use the following commands to interact with CEFS:

```shell
$ rubisco file1
```

This will execute file1's all callbacks registered in its `file_data` with all
arguments and options by default (if they are exists).

2. We can also pass arguments and options to the file:

```shell
$ rubisco --root=/ file2 hello -K=1
$ rubisco --root=/ dir1 -K=1 file3 Hello -X Test
```

When a CEFS file is executed, every parent directory's callbacks will be
executed ONLY for processing the passed options (like do some initialization
jobs) if dir_callbacks exists.
If we call rubisco by `rubisco --root=/ dir1 -K file3 -X Test`, file3_callback
will receive the following arguments:

```python
options = {"root": "/", "K": "1", "X": "Test"}
args = ["Hello"]
```

You can use URL to express this command:

```text
rubisco:///dir1/file3?root=/&K=1&X=Test#Hello
```

WARNING: We don't support same option name (even in different dir levels)
because it will cause confusion and conflict variable name in
`argparse.Namespace`. e.g. `rubisco --root=/ dir1 -K=1 file3 -K=2`.

3. We can also use symlink to create an alias for an event object:

```shell
$ rubisco --root=/ dir1 symlink1
```

This will execute symlink1's target, which is `/file1` in this case.
It's equivalent to:

```shell
$ rubisco --root=/ file1
```

4. We can also use mount point to mount external commands:

```shell
$ rubisco --root=/ mount1 update
$ rubisco --root=/ mount1 install python-is-python3
```

It will change the current working directory to `/` and execute the
`sudo apt update` and `sudo apt install python-is-python3` commands.

It's equivalent to:

```shell
$ cd / && sudo apt update
$ cd / && sudo apt install python-is-python3
```

"""

from rubisco.kernel.command_event.args import (
    Argument,
    DynamicArguments,
    Option,
    load_callback_args,
)
from rubisco.kernel.command_event.callback import (
    EventCallback,
    EventCallbackFunction,
)
from rubisco.kernel.command_event.cefs_fstab import mount_fstab
from rubisco.kernel.command_event.cmd_event import EventObject
from rubisco.kernel.command_event.event_file_data import EventFileData
from rubisco.kernel.command_event.event_path import EventPath
from rubisco.kernel.command_event.event_types import (
    EventObjectStat,
    EventObjectType,
    get_event_object_type_string,
)
from rubisco.kernel.command_event.register import EventUnit, register_events

__all__ = [
    "Argument",
    "DynamicArguments",
    "EventCallback",
    "EventCallbackFunction",
    "EventFileData",
    "EventObject",
    "EventObjectStat",
    "EventObjectType",
    "EventPath",
    "EventUnit",
    "Option",
    "get_event_object_type_string",
    "load_callback_args",
    "mount_fstab",
    "register_events",
]
