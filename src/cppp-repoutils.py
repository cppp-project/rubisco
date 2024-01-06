#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2023 The C++ Plus Project.
# This file is part of the cppp-repoutils.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
C++ Plus repository distributing, packaging and initialization utilities.

This module provides a set of utilities for initializing, distributing,
packaging and C++ Plus repositories. The utilities are designed for
develop C++ Plus source repositories and packages.
"""

import argparse
import gettext
import hashlib
import json
import locale
import shutil
import sys
import tempfile
import traceback
import subprocess
import os
import platform
import queue


# Application name.
APP_NAME = "cppp-repoutils"

# Application version.
APP_VERSION = (0, 1, 0)

# Text domain
TEXT_DOMAIN = APP_NAME

# Repository profile file.
REPO_PROFILE = "cppp-repo.json"

# Program file path.
PROGRAM_PATH = os.path.abspath(sys.argv[0])

# Python interpreter path.
PYTHON_PATH = sys.executable

# Is in PyInstaller environment.
IS_PYINSTALLER = getattr(sys, "frozen", False)

# Ignore file for dist.
DIST_IGNORE_FILE = ".cppprepo.ignore"


__author__ = "ChenPi11"
__copyright__ = "Copyright (C) 2023 The C++ Plus Project"
__license__ = "GPLv3-or-later"
__maintainer__ = "ChenPi11"
__url__ = "https://github.com/cppp-project/cppp-repoutils"
__version__ = "v" + ".".join(map(str, APP_VERSION))


# Gettext initialization.
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "../share/locale")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = os.path.join(os.path.dirname(__file__), "../locale")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR = "/usr/share/locale"
gettext.bindtextdomain(TEXT_DOMAIN, LOCALE_DIR)
gettext.textdomain(TEXT_DOMAIN)
_ = gettext.gettext


class Messages:
    """Messages class."""


# Messages.
messages = Messages()


# Stack
class Stack:
    """Stack class."""

    def __init__(self):
        """Initialize the stack."""

        self.__stack = []

    def push(self, item):
        """Push a new item to the stack.

        Args:
            item: The item to push.
        """

        self.__stack.append(item)

    def pop(self):
        """Pop the top item of the stack.

        Returns:
            The top item of the stack.
        """

        if len(self.__stack) == 0:
            return None
        return self.__stack.pop()

    def top(self):
        """Get the top item of the stack.

        Returns:
            The top item of the stack.
        """

        if len(self.__stack) == 0:
            return None
        return self.__stack[-1]

    def size(self):
        """Get the size of the stack.

        Returns:
            The size of the stack.
        """

        return len(self.__stack)

    def empty(self):
        """Check if the stack is empty.

        Returns:
            True if the stack is empty, otherwise False.
        """

        return len(self.__stack) == 0


# Output operations.


def colorize_output(file, color, text, end="\n"):
    """Colorize the output text.

    Args:
        file (file): The output file.
        color (str): The color of the output text.
        text (str): The output text.
        end (str): The end of the output text. (Default value is '\\n')
    """

    color_id = 0
    if color == "red":
        color_id = 31
    elif color == "green":
        color_id = 32
    elif color == "yellow":
        color_id = 33
    elif color == "blue":
        color_id = 34
    elif color == "magenta":
        color_id = 35
    elif color == "cyan":
        color_id = 36
    elif color == "gray":
        color_id = 90
    elif color == "white":
        color_id = 37
    file.write("\033[1;{}m{}\033[0m".format(color_id, text + end))


def progress_bar_update(current, total):
    """Update the progress bar.

    Args:
        current (int): The current progress.
        total (int): The total progress.
    """

    width = os.get_terminal_size().columns - 20

    if width <= 0:
        return

    if total == 0:
        return

    progress = current / total
    barsize = int(progress * width)

    if progress < 0.3:
        colorize_output(
            sys.stdout,
            "white",
            "[" + "=" * barsize + " " * (width - barsize) + "]",
            end="",
        )
    elif progress < 0.6:
        colorize_output(
            sys.stdout,
            "yellow",
            "[" + "=" * barsize + " " * (width - barsize) + "]",
            end="",
        )
    elif progress < 1:
        colorize_output(
            sys.stdout,
            "cyan",
            "[" + "=" * barsize + " " * (width - barsize) + "]",
            end="",
        )
    else:
        colorize_output(
            sys.stdout,
            "green",
            "[" + "=" * barsize + " " * (width - barsize) + "]",
            end="",
        )
    sys.stdout.write(" {:.2f}%".format(int(progress * 10000) / 100))
    sys.stdout.write("\r")
    sys.stdout.flush()
    if progress >= 1:
        sys.stdout.write("\n")
        sys.stdout.flush()


# Exception operations.


def print_list(extracted_list):  # Python3 traceback override
    """Print the list of tuples as returned by extract_tb() or
    extract_stack() as a formatted stack trace to the given file.

    Args:
        extracted_list (list): The list of tuples as returned by extract_tb() or extract_stack().

    Returns:
        str: The formatted stack trace.
    """

    res = "".join(traceback.StackSummary.from_list(extracted_list).format())
    return res


def get_exception():
    """Get more exception infomation.

    Returns:
        str: The exception infomation.
    """

    if sys.exc_info()[0] is None:
        return ""
    res = _("Traceback (most recent call last):") + "\n"
    res += print_list(traceback.extract_tb(sys.exc_info()[2])) + "\n"
    res += "{}: {}".format(sys.exc_info()[0].__name__, str(sys.exc_info()[1]))
    return res


def print_error():
    """Print exception infomation."""

    colorize_output(sys.stderr, "red", get_exception())


# Profile operations.


def load_profiles():
    """Load the repository profiles from the repository profile file.

    Returns:
        dict: A map of repository profiles.
    """

    configs = {}
    if not os.path.exists(REPO_PROFILE):
        colorize_output(
            sys.stdout,
            "red",
            _("Repository profile file '{file}' is not exist.").format(
                file=REPO_PROFILE
            ),
        )
        sys.exit(1)

    with open(REPO_PROFILE, "r", encoding="utf-8") as profile_file:
        configs = json.load(profile_file)
    return configs


# Repository profiles.
profiles = {}


# Shell operations.


# Which cache.
which_cache = {}


def which(program, strict=False):
    """Get the absolute program in the PATH or current directory.

    Args:
        program (str): The program.
        strict (bool): If True, raise an exception if the program is not found.

    Returns:
        str: The program path.
    """

    if program in which_cache:
        return which_cache[program]

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    if is_exe(program):
        return os.path.abspath(program)
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, program)
        if is_exe(exe_file):
            which_cache[program] = exe_file
            return os.path.abspath(exe_file)
    ext = os.path.splitext(program)[1]
    if platform.system() == "Windows" and ext != ".exe" and ext != ".com":
        # On Windows, 'xxx' may mean 'xxx.exe' or 'xxx.com' but 'xxx' is not in the PATH,
        # so we try add '.exe' or '.com' and find it again.
        result = which(program + ".exe", strict=False)
        if result == "":
            result = which(program + ".com", strict=False)
        if result != "":
            return result
    if strict:
        raise FileNotFoundError(
            _("Command '{cmd}' is not found. (Don't use alias)").format(cmd=program)
        )
    return ""


def shell_exec(command):
    """Find the shell in the PATH.

    Args:
        command (list): The command.

    Returns:
        list: Shell execute command
    """

    # Step 1: Check command[0] is a script.
    script = ""
    if len(command) > 0:
        script = command[0]
    if not os.path.exists(script):
        return command
    ext = os.path.splitext(script)[1]
    script_exts = [".sh", ".ps1", ".psm1", ".ps2", ".cmd", ".bat"]
    if ext not in script_exts:
        return command

    # Step 2: Find the shell in the PATH.
    shell = ""
    if platform.system() == "Windows":
        if ext in [".sh", ".ps1", ".psm1", ".ps2"]:
            shell = which("pwsh", strict=True)
            if shell == "":
                # New PowerShell is not installed. Use Windows PowerShell.
                shell = which("powershell", strict=True)
        elif ext in [".cmd", ".bat"]:
            shell = which("cmd", strict=True)
    else:
        # POSIX shells.
        if os.access(script, os.X_OK):
            # The script is executable, so we don't need to find the shell.
            return command

        # Try to read the first line of the script.
        try:
            with open(script, "r", encoding=locale.getencoding()) as file:
                line = file.readline()
                assert line.startswith("#!")
                shell = line[2:].strip()
                shell = which(shell, strict=True)
        except (UnicodeDecodeError, OSError, AssertionError):
            # Search by common shell's level.
            shells = ["zsh", "bash", "csh", "fish", "sh"]
            for shell in shells:
                shell = which(shell, strict=True)
                if shell != "":
                    break

    # Step 3: Replace the script with the shell.
    return [shell] + command


def exec_command(commands):
    """Execute the command in the shell.

    Args:
        commands: The command to execute.

    Returns:
        bool: True if the command is executed successfully, otherwise False.
    """

    try:
        commands = shell_exec(commands)
        colorize_output(sys.stdout, "cyan", str(commands))
        subprocess.check_call(commands)
    except subprocess.CalledProcessError:
        return False
    return True


def wget_save(url, file_path):
    """Download the file from the given url and save it to the given file path.

    Args:
        url (str): The url of the file to download.
        file_path (str): The file path to save the downloaded file.

    Returns:
        str: The file path of the downloaded file.
    """

    try:
        colorize_output(
            sys.stdout,
            "cyan",
            _("Downloading '{url}' to '{path}' ...").format(url=url, path=file_path),
        )
        exec_command(["wget", "-O", file_path, url])
    except subprocess.CalledProcessError:
        return ""
    return file_path


def tar_extract(file_path, extract_path):
    """Extract the tar file to the given path.

    Args:
        file_path (str): The path of the tar file to extract.
        extract_path (str): The path to extract the tar file.

    Returns:
        bool: True if the tar file is extracted successfully, otherwise False.
    """

    try:
        colorize_output(
            sys.stdout,
            "cyan",
            _("Extracting '{filepath}' to '{extractpath}' ...").format(
                filepath=file_path, extractpath=extract_path
            ),
        )
        exec_command(["tar", "-zxvf", file_path, "-C", extract_path])
    except subprocess.CalledProcessError:
        return False
    return True


def get_arch():
    """Get the architecture of the operating system.

    Returns:
        str: The architecture of the operating system.
    """

    arch = platform.machine().lower()
    arch = variables.get("arch", arch)
    if arch == "all":
        return "unknown"
    return arch


# File operations.


def list_all_files(dir_path):
    """Recursively list all files in the given directory.

    Args:
        dir_path (str): The path of the directory to list.

    Returns:
        list: A list of all files in the given directory.
    """

    files = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            files.extend(list_all_files(os.path.join(dir_path, file)))
        else:
            files.append(os.path.abspath(os.path.join(dir_path, file)))
    return files


def sum_file_md5(file_path):
    """Sum the md5 of the given file.

    Args:
        file_path (str): The path of the file to sum.

    Returns:
        str: The md5 of the given file.
    """

    with open(file_path, "rb") as file:
        md5 = hashlib.md5()
        md5.update(file.read())
        return md5.hexdigest()


def sum_files_md5(dir_path):
    """Recursively sum all file's md5 of the given directory.

    Args:
        dir_path (str): The path of the directory to sum.

    Returns:
        str: The md5 of all files in the given directory.
    """

    md5s = {}
    for file in list_all_files(dir_path):
        md5s[file] = sum_file_md5(file)
    return md5s


def get_dir_size(dir_path):
    """Recursively get the size of the given directory.

    Args:
        dir_path (str): The path of the directory to get size.

    Returns:
        int: The size of the given directory.
    """

    size = 0
    for file in list_all_files(dir_path):
        size += os.path.getsize(file)
    return size


# Temporary files.
temp_files = queue.Queue()


def register_temp_path(path):
    """Register the temporary path to delete when the program exit.

    Args:
        path (str): The path to register.
    """

    temp_files.put(os.path.abspath(path))


def delete_all_temps():
    """Delete all registered temporaries."""
    while not temp_files.empty():
        path = temp_files.get()
        if os.path.exists(path):
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except OSError:
                    pass
            else:
                try:
                    os.remove(path)
                except OSError:
                    pass


# Variable operations.


# Variables
variables = {}


def push_variables(name, value):
    """Push a new variable.

    Args:
        name (str): The name of the variable.
        value (str): The value of the variable.
    """

    if name in variables:
        variables[name].push(value)
    else:
        variables[name] = Stack()
        variables[name].push(value)


def pop_variables(name):
    """Pop the top value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The top value of the given variable.
    """

    if name in variables:
        return variables[name].pop()
    return None


def get_variable(name):
    """Get the value of the given variable.

    Args:
        name (str): The name of the variable.

    Returns:
        str: The value of the given variable.
    """

    if name in variables:
        return variables[name].top()
    raise KeyError(repr(name))


def format_string_with_variables(string):
    """Format the string with variables.

    Args:
        string (str): The string to format.

    Returns:
        str: The formatted string.
    """

    if not isinstance(string, str):
        return string

    for name, values in variables.items():
        string = string.replace("$" + name, values.top())

    return string


# FormatMap
class FormatMap(dict):
    """FormatMap class."""

    def __init__(self, *args, **kwargs):
        """Initialize the FormatMap."""

        super().__init__(*args, **kwargs)

    def get(self, key, *args):
        """Get the value of the given key.

        Args:
            key (str): The key to get value.
            default (str): The default value.

        Returns:
            str: The value of the given key.
        """

        if not key in self.keys() and len(args) == 0:
            raise KeyError(repr(key))
        if not key in self.keys() and len(args) == 1:
            return format_string_with_variables(args[0])
        return format_string_with_variables(super().get(key))

    def __getitem__(self, key):
        """Get the value of the given key.

        Args:
            key (str): The key to get value.

        Returns:
            str: The value of the given key.
        """

        return self.get(key)

    @staticmethod
    def from_dict(src):
        """Create a FormatMap from the given dict.

        Args:
            src (dict): The dict to create FormatMap.

        Returns:
            FormatMap: The created FormatMap.
        """

        var_map = FormatMap()
        for key, value in src.items():
            var_map[key] = value
        return var_map


# Package operations.


def setup_subpackages():
    """Setup subpackages of the repository."""

    sub_packages = profiles.get("subpackages", [])

    all_count = len(sub_packages)
    suc_count = 0
    err_count = 0
    ign_count = 0
    new_count = 0

    for pkg in sub_packages:
        try:
            if os.path.exists(sub_packages[pkg]["path"]):
                colorize_output(
                    sys.stdout,
                    "green",
                    _("Module '{module}' is already setup.").format(module=pkg),
                )
                new_count += 1
                continue
            colorize_output(
                sys.stdout,
                "white",
                _("Setting up package: '{package}' ...").format(package=pkg),
            )
            colorize_output(
                sys.stdout,
                "white",
                _("\tPath: {path}").format(path=sub_packages[pkg]["path"]),
            )
            colorize_output(
                sys.stdout,
                "white",
                _("\tDescription: {description}").format(
                    description=sub_packages[pkg]["description"]
                ),
            )
            colorize_output(
                sys.stdout,
                "white",
                _("\tUrl: {url}").format(url=sub_packages[pkg]["remote-url"]),
            )

            if sub_packages[pkg]["remote"] == "git":
                # Git repository.
                colorize_output(sys.stdout, "white", _("\tType: Git"))
                if not exec_command(
                    [
                        "git",
                        "clone",
                        "-b",
                        sub_packages[pkg]["git-branch"],
                        sub_packages[pkg]["remote-url"],
                        sub_packages[pkg]["path"],
                    ]
                ):
                    colorize_output(
                        sys.stdout, "red", _("Failed to clone the repository.")
                    )
                    err_count += 1
                    continue

            elif sub_packages[pkg]["remote"] == "svn":
                # Subversion repository.
                colorize_output(sys.stdout, "white", _("\tType: Svn"))
                if not exec_command(
                    [
                        "svn",
                        "checkout",
                        "-r",
                        sub_packages[pkg]["svn-revision"],
                        sub_packages[pkg]["remote-url"],
                        sub_packages[pkg]["path"],
                    ]
                ):
                    colorize_output(
                        sys.stdout, "red", _("Failed to checkout the repository.")
                    )
                    err_count += 1
                    continue
            elif sub_packages[pkg]["remote"] == "tgz-archive":
                # Tar.GZip archive file
                colorize_output(sys.stdout, "white", _("\tType: Archive"))
                if not os.path.exists(sub_packages[pkg]["path"]):
                    os.makedirs(sub_packages[pkg]["path"])
                    temp_archive_file = tempfile.mktemp(".tar.gz", "cppp-repo-")
                    register_temp_path(temp_archive_file)
                    wget_save(sub_packages[pkg]["remote-url"], temp_archive_file)
                    tar_extract(temp_archive_file, sub_packages[pkg]["path"])
                    os.remove(temp_archive_file)
            else:
                err_count += 1
                colorize_output(sys.stdout, "red", _("Unknown remote type."))
                continue
            colorize_output(
                sys.stdout,
                "green",
                _("Module '{module}' is set up successfully.").format(module=pkg),
            )
            suc_count += 1
        except KeyboardInterrupt:
            ign_count += 1
            colorize_output(sys.stdout, "red", _("Interrupted by user."))
            try:
                shutil.rmtree(sub_packages[pkg]["path"])
            except OSError:
                pass
            continue
        except (OSError, subprocess.CalledProcessError):
            err_count += 1
            colorize_output(
                sys.stdout,
                "red",
                _("Failed to setup module '{module}'.").format(module=pkg),
            )
            print_error()
            try:
                shutil.rmtree(sub_packages[pkg]["path"])
            except OSError:
                pass
            continue

    colorize_output(
        sys.stdout,
        "white",
        _(
            "Setup {all} package(s), success: {suc}, error: {err}, ignored: {ign}, latest: {lts}."
        ).format(
            all=all_count, suc=suc_count, err=err_count, ign=ign_count, lts=new_count
        ),
    )


def deinit_subpackages():
    """Deinitialize subpackages of the repository."""

    sub_packages = profiles.get("subpackages", [])

    all_count = len(sub_packages)
    suc_count = 0
    err_count = 0
    ign_count = 0

    colorize_output(
        sys.stdout, "yellow", _("The following modules will be deinitialized:")
    )
    for pkg in sub_packages:
        colorize_output(sys.stdout, "blue", "\t" + pkg)
    colorize_output(
        sys.stdout,
        "yellow",
        _("ALL THINGS OF SUBPACKAGES WILL BE LOST!\nAre you sure to continue? [Y/n] "),
        end="",
    )
    if input() != "Y":
        colorize_output(sys.stdout, "red", _("Deinitialization is canceled."))
        return

    for pkg in sub_packages:
        try:
            if not os.path.exists(sub_packages[pkg]["path"]):
                colorize_output(
                    sys.stdout,
                    "while",
                    _("Module '{module}' is not exist, ignored.").format(module=pkg),
                )
                ign_count += 1
                continue
            shutil.rmtree(sub_packages[pkg]["path"])
            suc_count += 1
            colorize_output(
                sys.stdout,
                "green",
                _("Module '{module}' is deinitialized successfully.").format(
                    module=pkg
                ),
            )
        except KeyboardInterrupt:
            ign_count += 1
            colorize_output(sys.stdout, "red", _("Interrupted by user."))
            continue
        except OSError as error:
            err_count += 1
            colorize_output(
                sys.stdout,
                "red",
                _("Failed to deinitialize module '{module}': ").format(module=pkg),
            )
            colorize_output(sys.stdout, "red", str(error))

    colorize_output(
        sys.stdout,
        "white",
        _(
            "Deinitialized {all} package(s), success: {suc}, error: {err}, ignored: {ign}."
        ).format(all=all_count, suc=suc_count, err=err_count, ign=ign_count),
    )


def print_package_info():
    """Print the package information."""

    colorize_output(
        sys.stdout, "white", _("Name: {name}").format(name=profiles["name"])
    )
    colorize_output(
        sys.stdout, "white", _("Version: {ver}").format(ver=profiles["version"])
    )
    colorize_output(
        sys.stdout,
        "white",
        _("Description: {description}").format(description=profiles["description"]),
    )
    colorize_output(
        sys.stdout, "white", _("License: {license}").format(license=profiles["license"])
    )
    colorize_output(
        sys.stdout,
        "white",
        _("Author(s): {authors}").format(authors=", ".join(profiles["authors"])),
    )
    colorize_output(
        sys.stdout, "white", _("Webpage: {webpage}").format(profiles["webpage"])
    )


# Package dist operations.

# TODO: parse_ignorefile
'''def parse_ignorefile(filepath):
    """
    Parse ignore file.
    """

    ign_list = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("#include "):
                inc_file = line.replace("#include", "")
                if not os.path.isfile(inc_file):
                    colorize_output(sys.stdout, "yellow")'''


def make_subpackage_dist(subpackage, distdir):
    """Make the distribution package of the given subpackage.

    Args:
        subpackage (str): The name of the subpackage.
    """

    commands = [PYTHON_PATH] if IS_PYINSTALLER else [PYTHON_PATH, PROGRAM_PATH]
    commands.extend(
        [
            "--root",
            profiles["subpackages"][subpackage]["path"],
            "dist",
            "--distdir",
            os.path.abspath(os.path.join(distdir, subpackage)),
        ]
    )
    exec_command(commands)


def make_dist(distdir):
    """Make the distribution package.

    Args:
        distdir (str): The directory to save the distribution package.
    """

    colorize_output(
        sys.stdout,
        "white",
        _("Making distribution package for '{pkg}' ...").format(pkg=profiles["name"]),
    )
    file_list_file = profiles["file-list"]
    file_list = []
    with open(file_list_file, "r", encoding="utf-8") as file:
        file_list = file.read().strip().split("\n")

    all_count = len(file_list)
    suc_count = 0

    try:
        # Clean and make the distribution directory.
        if os.path.exists(distdir):
            colorize_output(
                sys.stdout,
                "white",
                _("Distribution directory is already exist, removing it ..."),
            )
            shutil.rmtree(distdir)
        os.makedirs(distdir)

        # Copy files.
        progress_bar_update(0, 0)
        for file in file_list:
            file_dir = os.path.dirname(file)
            if not os.path.exists(os.path.join(distdir, file_dir)):
                os.makedirs(os.path.join(distdir, file_dir))
            shutil.copy(file, os.path.join(distdir, file))
            suc_count += 1
            progress_bar_update(suc_count, all_count)

        colorize_output(
            sys.stdout, "green", _("Distribution package is made successfully.")
        )
        colorize_output(
            sys.stdout,
            "white",
            _("Copied {suc} files to '{path}'.").format(suc=suc_count, path=distdir),
        )

        # Copy subpackages.
        sub_packages = profiles.get("subpackages", [])
        for pkg in sub_packages:
            make_subpackage_dist(pkg, distdir)
    except KeyboardInterrupt:
        colorize_output(sys.stdout, "red", _("Interrupted by user."))
        try:
            shutil.rmtree(distdir)
        except OSError:
            pass
    except (OSError, subprocess.CalledProcessError):
        try:
            shutil.rmtree(distdir)
        except OSError:
            pass
        colorize_output(sys.stdout, "red", _("Failed to make distribution package."))
        print_error()
        return


def build_profile(dist_profile):
    """Build the project.

    Args:
        dist_profile (FormatMap): The path of the distribution profile.
    """

    build_script = dist_profile["posix-build-script"]
    if platform.system() == "Windows":
        build_script = dist_profile["windows-build-script"]
    bin_dir = dist_profile["bin-dir"]

    # Build the package.
    colorize_output(sys.stdout, "white", _("Building package ..."))
    exec_command([os.path.abspath(os.path.join(build_script))])
    if not os.path.exists(bin_dir):
        colorize_output(
            sys.stdout, "red", _("Path '{path}' is not exist.").format(path=bin_dir)
        )
        sys.exit(1)
    else:
        colorize_output(
            sys.stdout,
            "green",
            _("Package is built successfully, installed to '{path}'.").format(
                path=bin_dir
            ),
        )
    return bin_dir


def build_project(profile_file):
    """Build the package.

    Args:
        profile_file (str): The path of the distribution profile.
    """

    dist_profile = FormatMap()
    with open(profile_file, "r", encoding="utf-8") as file:
        dist_profile = FormatMap.from_dict(json.load(file))

    colorize_output(
        sys.stdout,
        "white",
        _("Building '{pkg}' by profile '{path}' ...").format(
            pkg=profiles["name"], path=profile_file
        ),
    )

    build_profile(dist_profile)

    next_profile_path = dist_profile.get("next-profile", "")
    if next_profile_path != "":
        if os.path.abspath(next_profile_path) == os.path.abspath(profile_file):
            colorize_output(
                sys.stdout,
                "red",
                _("Next profile is the same as current profile, ignored."),
            )
            sys.exit(1)
        build_project(next_profile_path)


def make_deb(dist_profile, arch):
    """Make the Debian package.

    Args:
        dist_profile (FormatMap): The path of the distribution profile.
        arch (str): The architecture of the package.
    """

    if arch == "unknown":
        arch = "all"
    tempdir = tempfile.mkdtemp(".deb", "cppp-repo-")
    register_temp_path(tempdir)
    os.makedirs(os.path.join(tempdir, "DEBIAN"))
    os.makedirs(os.path.join(tempdir, "usr"))

    # Change arch to Debian format.
    debian_format = {
        "arm": "armhf",
        "x86_64": "amd64",
        "aarch64": "arm64",
        "loongarch64": "loong64",
        "powerpc64": "ppc64",
        "powerpc64le": "ppc64el",
    }
    arch = debian_format.get(arch, arch)

    # Build the project.
    bin_dir = build_profile(dist_profile)

    # Copy files.
    colorize_output(sys.stdout, "white", _("Copying files ..."))
    for file in list_all_files(bin_dir):
        file_rel = os.path.relpath(file, bin_dir)
        file_dir = os.path.dirname(file_rel)
        if not os.path.exists(os.path.join(tempdir, "usr", file_dir)):
            os.makedirs(os.path.join(tempdir, "usr", file_dir))
        shutil.copy(file, os.path.join(tempdir, "usr", file_rel), follow_symlinks=False)

    # Generate control file.
    package = dist_profile.get("deb-name", profiles["name"])
    version = profiles["version"]
    if version[0] == "v":
        version = version[1:]

    maintainer = ", ".join(profiles["authors"])
    description = profiles["description"]

    installed_size = dist_profile.get("installed-size", "")
    priority = dist_profile.get("priority", "optional")
    homepage = profiles.get("webpage", "")
    section = dist_profile.get("section", "")
    depends = dist_profile.get("deb-depends", "")
    recommends = dist_profile.get("deb-recommends", "")
    suggests = dist_profile.get("deb-suggests", "")
    enhances = dist_profile.get("deb-enhances", "")
    breaks = dist_profile.get("deb-breaks", "")
    conflicts = dist_profile.get("deb-conflicts", "")
    pre_depends = dist_profile.get("deb-pre-depends", "")

    deb_control_data = """Package: {pkg}
Version: {ver}
Architecture: {arch}
Maintainer: {maintainer}
Description: {description}
Essential: no
"""
    control_data = deb_control_data.format(
        pkg=package,
        ver=version,
        arch=arch,
        maintainer=maintainer,
        description=description,
    )

    if priority != "":
        control_data += "Priority: {priority}\n".format(priority=priority)
    if installed_size != "":
        if installed_size == "auto":
            installed_size = get_dir_size(os.path.join(tempdir, "usr")) // 1024
        control_data += "Installed-Size: {size}\n".format(size=installed_size)
    if homepage != "":
        control_data += "Homepage: {homepage}\n".format(homepage=homepage)
    if section != "":
        control_data += "Section: {section}\n".format(section=section)
    if depends != "":
        control_data += "Depends: {depends}\n".format(depends=depends)
    if recommends != "":
        control_data += "Recommends: {recommends}\n".format(recommends=recommends)
    if suggests != "":
        control_data += "Suggests: {suggests}\n".format(suggests=suggests)
    if enhances != "":
        control_data += "Enhances: {enhances}\n".format(enhances=enhances)
    if breaks != "":
        control_data += "Breaks: {breaks}\n".format(breaks=breaks)
    if conflicts != "":
        control_data += "Conflicts: {conflicts}\n".format(conflicts=conflicts)
    if pre_depends != "":
        control_data += "Pre-Depends: {pre_depends}\n".format(pre_depends=pre_depends)
    with open(
        os.path.join(tempdir, "DEBIAN", "control"), "w", encoding="utf-8"
    ) as file:
        file.write(control_data)

    # Generate md5sums file.
    colorize_output(
        sys.stdout, "white", _("Generating '{file}'  ...").format(file="md5sums")
    )
    md5s = sum_files_md5(os.path.join(tempdir, "usr"))
    for file, md5 in md5s.items():
        colorize_output(
            sys.stdout, "gray", "{}: {}".format(os.path.relpath(file, tempdir), md5)
        )
    md5sums_data = ""
    for file, md5 in md5s.items():
        md5sums_data += "{} {}\n".format(md5, os.path.relpath(file, tempdir))
    with open(
        os.path.join(tempdir, "DEBIAN", "md5sums"), "w", encoding="utf-8"
    ) as file:
        file.write(md5sums_data)

    # Copy preinst file.
    preinst_file = dist_profile.get("posix-pre-install-script", "")
    if preinst_file != "":
        colorize_output(sys.stdout, "white", _("Copying preinst file ..."))
        shutil.copy(preinst_file, os.path.join(tempdir, "DEBIAN", "preinst"))

    # Copy prerm file.
    prerm_file = dist_profile.get("posix-pre-remove-script", "")
    if prerm_file != "":
        colorize_output(sys.stdout, "white", _("Copying prerm file ..."))
        shutil.copy(prerm_file, os.path.join(tempdir, "DEBIAN", "prerm"))

    # Copy postinst file.
    postinst_file = dist_profile.get("posix-post-install-script", "")
    if postinst_file != "":
        colorize_output(sys.stdout, "white", _("Copying postinst file ..."))
        shutil.copy(postinst_file, os.path.join(tempdir, "DEBIAN", "postinst"))

    # Copy postrm file.
    postrm_file = dist_profile.get("posix-post-remove-script", "")
    if postrm_file != "":
        colorize_output(sys.stdout, "white", _("Copying postrm file ..."))
        shutil.copy(postrm_file, os.path.join(tempdir, "DEBIAN", "postrm"))

    # Build the package.
    colorize_output(sys.stdout, "white", _("Building package ..."))
    output_pkg_path = dist_profile["output-package-path"]
    output_pkg_dir = os.path.dirname(output_pkg_path)
    if not os.path.exists(output_pkg_dir):
        os.makedirs(output_pkg_dir)
    exec_command(["dpkg-deb", "--build", tempdir, output_pkg_path])

    colorize_output(sys.stdout, "green", _("Package is built successfully."))


def make_distpkg(pkgtype, profile_file):
    """Make binary dist package.

    Args:
        pkgtype (str): Package type.
        profile_file (str): The path of the distribution profile.
    """

    dist_profile = FormatMap()
    with open(profile_file, "r", encoding="utf-8") as file:
        dist_profile = FormatMap.from_dict(json.load(file))

    colorize_output(
        sys.stdout,
        "white",
        _("Making '{type}' binary distribution package by profile '{path}' ...").format(
            type=pkgtype, path=profile_file
        ),
    )

    arch = get_variable("arch")
    if dist_profile.get("cross-arch", False):
        arch = "unknown"
        push_variables("arch", "unknown")
        colorize_output(
            sys.stdout,
            "white",
            _(
                "This program can run on all architectures, so we set 'arch' to unknown."
            ),
        )
    else:
        push_variables("arch", arch)

    colorize_output(sys.stdout, "gray", _("Architecture: {arch}").format(arch=arch))
    if pkgtype == "dpkg":
        make_deb(dist_profile, arch)
    else:
        colorize_output(
            sys.stdout, "red", _("Unknown package type '{type}'.").format(type=pkgtype)
        )
        sys.exit(1)

    next_profile_path = dist_profile.get("next-profile", "")
    if next_profile_path != "":
        if os.path.abspath(next_profile_path) == os.path.abspath(profile_file):
            colorize_output(
                sys.stdout,
                "red",
                _("Next profile is the same as current profile, ignored."),
            )
            sys.exit(1)
        make_distpkg(pkgtype, next_profile_path)
    pop_variables("arch")


# Argument parser.
arg_parser = argparse.ArgumentParser(
    description=_(
        "C++ Plus repository distributing, packaging and initialization utilities."
    )
)
arg_parser.add_argument(
    "--root", default=".", help=_("The root directory of the repository.")
)
subparsers = arg_parser.add_subparsers(
    dest="command", help=_("The command to execute.")
)
subparsers.add_parser("init", help=_("Initialize all required C++ Plus repository."))
subparsers.add_parser(
    "deinit", help=_("Deinitialize all required C++ Plus repository.")
)
subparsers.add_parser("info", help=_("Print the package information."))
dist_parser = subparsers.add_parser(
    "dist", help=_("Make the source distribution package.")
)
dist_parser.add_argument(
    "--distdir",
    default="$name-$version",
    help=_("The directory to save the distribution package, support variables."),
)

distpkg_parser = subparsers.add_parser(
    "distpkg", help=_("Make the distribution package.")
)
distpkg_parser.add_argument("--type", default="", help=_("Make the Debian package."))
# TODO: Build should support build flags.

build_parser = subparsers.add_parser("build", help=_("Build the package."))
# TODO: Build should support build flags.

var_parser = arg_parser.add_argument_group("variable")
var_parser.add_argument(
    "--var",
    "-V",
    action="append",
    default=[],
    help=_("Set a variable, format: --var name"),
)

arg_parser.add_argument(
    "--version",
    "-v",
    action="store_true",
    default=False,
    help=_("Print the version of the program."),
)

# Main entry.


# Version string.
VERSION_STRING = _(
    """{name} {ver}
{copyright}
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
Written by {author}."""
)


def main():
    """The main function of the repoutil module."""

    global profiles
    args = arg_parser.parse_args()
    os.chdir(os.path.abspath(args.root))

    # Checking for non-repo-operation commands.
    if args.version:
        colorize_output(
            sys.stdout,
            "white",
            VERSION_STRING.format(
                name=APP_NAME,
                ver=__version__,
                copyright=__copyright__,
                author=__author__,
            ),
        )
        return 0

    # Load repository profiles.
    profiles = load_profiles()

    # Set variables.
    push_variables("arch", get_arch())
    push_variables("name", profiles["name"])
    push_variables("root", os.path.abspath(os.curdir))
    push_variables("version", profiles["version"])
    for var in args.var:
        key, value = var.split("=")
        colorize_output(
            sys.stdout,
            "gray",
            _("Loaded variable: {key} = '{val}'").format(key=key, val=value),
        )
        push_variables(key, value)
    # Architecture cannot be 'all'.
    if get_variable("arch") == "all":
        push_variables("arch", "unknown")

    # Checking for repo-operation commands.
    if args.command == "init":
        setup_subpackages()
    elif args.command == "deinit":
        deinit_subpackages()
    elif args.command == "info":
        print_package_info()
    elif args.command == "dist":
        make_dist(format_string_with_variables(args.distdir))
    elif args.command == "distpkg":
        if args.type == "":
            colorize_output(sys.stdout, "red", _("Required options --type [dpkg]"))
        else:
            make_distpkg(args.type, profiles["dist-profile"])
    elif args.command == "build":
        build_project(profiles["dist-profile"])
    else:
        print_package_info()
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(3)
    finally:
        delete_all_temps()
