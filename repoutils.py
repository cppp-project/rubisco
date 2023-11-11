#!/usr/bin/env python3

# Copyright (C) 2023 The C++ Plus Project.
# This file is part of the cppp-reiconv library.
#
# The cppp-reiconv library is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# The cppp-reiconv library is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with the cppp-reiconv library; see the file COPYING.
# If not, see <https://www.gnu.org/licenses/>.

"""
C++ Plus repository distributing, packaging and initialization utilities.

This module provides a set of utilities for initializing, distributing, packaging and
C++ Plus repositories. The utilities are designed for develop
C++ Plus source repositories and packages.
"""

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import traceback
import subprocess
import os
import platform
import queue


# Repository profile file.
REPO_PROFILE = "cppp-repo.json"

# Program file path.
program_path = os.path.abspath(sys.argv[0])

# Python interpreter path.
python_path = sys.executable

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


def colorize_output(file, color, text):
    """Colorize the output text.

    Args:
        file (file): The output file.
        color (str): The color of the output text.
        text (str): The output text.
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
    elif color == "white":
        color_id = 37
    file.write("\033[1;%dm%s\033[0m" % (color_id, text))


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
    bar = int(progress * width)

    if progress < 0.3:
        colorize_output(
            sys.stdout, "white", "[" + "=" * bar + " " * (width - bar) + "]"
        )
    elif progress < 0.6:
        colorize_output(
            sys.stdout, "yellow", "[" + "=" * bar + " " * (width - bar) + "]"
        )
    elif progress < 1:
        colorize_output(sys.stdout, "cyan", "[" + "=" * bar + " " * (width - bar) + "]")
    else:
        colorize_output(
            sys.stdout, "green", "[" + "=" * bar + " " * (width - bar) + "]"
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
    res = ""
    for item in traceback.StackSummary.from_list(extracted_list).format():
        res += item
    return res


def get_exception():
    """Get more exception infomation.

    Returns:
        str: The exception infomation.
    """

    if sys.exc_info()[0] is None:
        return ""
    res = "Traceback(most recent call last):\n"
    res += print_list(traceback.extract_tb(sys.exc_info()[2]))
    res += sys.exc_info()[0].__name__ + ": " + str(sys.exc_info()[1])
    return res


def print_error():
    """Print exception infomation."""

    colorize_output(sys.stderr, "red", get_exception() + "\n")


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
            "Repository profile file '%s' is not exist.\n" % (REPO_PROFILE),
        )
        sys.exit(1)

    with open(REPO_PROFILE, "r", encoding="utf-8") as profile_file:
        configs = json.load(profile_file)
    return configs


# Repository profiles.
profiles = {}

# Shell operations.


def exec_command(commands):
    """Execute the command in the shell.

    Args:
        commands: The command to execute.

    Returns:
        bool: True if the command is executed successfully, otherwise False.
    """

    try:
        colorize_output(sys.stdout, "cyan", str(commands) + "\n")
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
            sys.stdout, "cyan", "Downloading '%s' to '%s' ...\n" % (url, file_path)
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
            "Extracting '%s' to '%s' ...\n" % (file_path, extract_path),
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

    arch = platform.machine()
    return arch.lower()


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

    with open(file_path, mode="rb") as f:
        md5 = hashlib.md5()
        md5.update(f.read())
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
                except:
                    pass
            else:
                try:
                    os.remove(path)
                except:
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

    if name in variables.keys():
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

    if name in variables.keys():
        return variables[name].pop()
    return None

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
        elif not key in self.keys() and len(args) == 1:
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
                    sys.stdout, "green", "Module '%s' is already setup.\n" % (pkg)
                )
                new_count += 1
                continue
            colorize_output(
                sys.stdout, "white", "Setting up package: '%s' ...\n" % (pkg)
            )
            colorize_output(
                sys.stdout, "white", "  Path: %s\n" % (sub_packages[pkg]["path"])
            )
            colorize_output(
                sys.stdout,
                "white",
                "  Description: %s\n" % (sub_packages[pkg]["description"]),
            )
            colorize_output(
                sys.stdout, "white", "  Url: %s\n" % (sub_packages[pkg]["remote-url"])
            )

            if sub_packages[pkg]["remote"] == "git":
                # Git repository.
                colorize_output(sys.stdout, "white", "  Type: Git\n")
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
                        sys.stdout, "red", "Failed to clone the repository.\n"
                    )
                    err_count += 1
                    continue

            elif sub_packages[pkg]["remote"] == "svn":
                # Subversion repository.
                colorize_output(sys.stdout, "white", "  Type: Svn\n")
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
                        sys.stdout, "red", "Failed to checkout the repository.\n"
                    )
                    err_count += 1
                    continue
            elif sub_packages[pkg]["remote"] == "tgz-archive":
                # Tar.GZip archive file
                colorize_output(sys.stdout, "white", "  Type: Archive\n")
                if not os.path.exists(sub_packages[pkg]["path"]):
                    os.makedirs(sub_packages[pkg]["path"])
                    temp_archive_file = tempfile.mktemp(".tar.gz", "cppp-repo-")
                    register_temp_path(temp_archive_file)
                    wget_save(sub_packages[pkg]["remote-url"], temp_archive_file)
                    tar_extract(temp_archive_file, sub_packages[pkg]["path"])
                    os.remove(temp_archive_file)
            else:
                err_count += 1
                colorize_output(sys.stdout, "red", "Unknown remote type.\n")
                continue
            colorize_output(
                sys.stdout, "green", "Module '%s' is set up successfully.\n" % (pkg)
            )
            suc_count += 1
        except KeyboardInterrupt:
            ign_count += 1
            colorize_output(sys.stdout, "red", "Interrupted.\n")
            try:
                shutil.rmtree(sub_packages[pkg]["path"])
            except OSError:
                pass
            continue
        except (OSError, subprocess.CalledProcessError):
            err_count += 1
            colorize_output(sys.stdout, "red", "Failed to setup module '%s': " % (pkg))
            print_error()
            try:
                shutil.rmtree(sub_packages[pkg]["path"])
            except OSError:
                pass
            continue

    colorize_output(
        sys.stdout,
        "white",
        "Setup %d package(s), success: %d, error: %d, ignored: %d, latest: %d\n"
        % (all_count, suc_count, err_count, ign_count, new_count),
    )


def deinit_subpackages():
    """Deinitialize subpackages of the repository."""

    sub_packages = profiles.get("subpackages", [])

    all_count = len(sub_packages)
    suc_count = 0
    err_count = 0
    ign_count = 0

    colorize_output(
        sys.stdout, "yellow", "The following modules will be deinitialized:\n"
    )
    for pkg in sub_packages:
        colorize_output(sys.stdout, "blue", "  %s\n" % (pkg))
    colorize_output(
        sys.stdout,
        "yellow",
        "ALL THINGS OF SUBPACKAGES WILL BE LOST!\nAre you sure to continue? [Y/n] ",
    )
    if input() != "Y":
        colorize_output(sys.stdout, "red", "Deinitialization is canceled.\n")
        return

    for pkg in sub_packages:
        try:
            if not os.path.exists(sub_packages[pkg]["path"]):
                colorize_output(
                    sys.stdout, "while", "Module '%s' is not exist, ignored.\n" % (pkg)
                )
                ign_count += 1
                continue
            shutil.rmtree(sub_packages[pkg]["path"])
            suc_count += 1
            colorize_output(
                sys.stdout,
                "green",
                "Module '%s' is deinitialized successfully.\n" % (pkg),
            )
        except KeyboardInterrupt:
            ign_count += 1
            colorize_output(sys.stdout, "red", "Interrupted.\n")
            continue
        except OSError as e:
            err_count += 1
            colorize_output(
                sys.stdout, "red", "Failed to deinitialize module '%s': " % (pkg)
            )
            colorize_output(sys.stdout, "red", str(e) + "\n")

    colorize_output(
        sys.stdout,
        "white",
        "Deinitialized %d package(s), success: %d, error: %d, ignored: %d\n"
        % (all_count, suc_count, err_count, ign_count),
    )


def print_package_info():
    """Print the package information."""

    colorize_output(sys.stdout, "white", "Name: %s\n" % profiles["name"])
    colorize_output(sys.stdout, "white", "Version: %s\n" % profiles["version"])
    colorize_output(sys.stdout, "white", "Description: %s\n" % profiles["description"])
    colorize_output(sys.stdout, "white", "License: %s\n" % profiles["license"])
    colorize_output(
        sys.stdout, "white", "Author(s): %s\n" % ", ".join(profiles["authors"])
    )
    colorize_output(sys.stdout, "white", "Webpage: %s\n" % profiles["webpage"])


def make_subpackage_dist(subpackage, distdir):
    """Make the distribution package of the given subpackage.

    Args:
        subpackage (str): The name of the subpackage.
    """

    exec_command(
        [
            python_path,
            program_path,
            "--root",
            profiles["subpackages"][subpackage]["path"],
            "dist",
            "--distdir",
            os.path.abspath(os.path.join(distdir, subpackage)),
        ]
    )


def make_dist(distdir):
    """Make the distribution package.

    Args:
        distdir (str): The directory to save the distribution package.
    """

    colorize_output(
        sys.stdout,
        "white",
        "Making distribution package for %s ...\n" % profiles["name"],
    )
    file_list_file = profiles["file-list"]
    file_list = []
    with open(file_list_file, mode="r", encoding="utf-8") as f:
        file_list = f.read().strip().split("\n")

    all_count = len(file_list)
    suc_count = 0

    try:
        # Clean and make the distribution directory.
        if os.path.exists(distdir):
            colorize_output(
                sys.stdout,
                "white",
                "Distribution directory is already exist, removing it ...\n",
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
            sys.stdout, "green", "Distribution package is made successfully.\n"
        )
        colorize_output(
            sys.stdout, "white", "Copied %d files to '%s'.\n" % (suc_count, distdir)
        )

        # Copy subpackages.
        sub_packages = profiles.get("subpackages", [])
        for pkg in sub_packages:
            make_subpackage_dist(pkg, distdir)
    except KeyboardInterrupt:
        colorize_output(sys.stdout, "red", "\nInterrupted.\n")
        try:
            shutil.rmtree(distdir)
        except OSError:
            pass
    except (OSError, subprocess.CalledProcessError):
        try:
            shutil.rmtree(distdir)
        except OSError:
            pass
        colorize_output(sys.stdout, "red", "Failed to make distribution package\n")
        print_error()
        return


def make_deb(dist_profile):
    """Make the Debian package.

    Args:
        pkg_root (str): The root directory of the package.
        dist_profile (FormatMap): The path of the distribution profile.
    """

    tempdir = tempfile.mkdtemp(".deb", "cppp-repo-")
    register_temp_path(tempdir)
    os.makedirs(os.path.join(tempdir, "DEBIAN"))
    os.makedirs(os.path.join(tempdir, "usr"))

    arch = get_arch()
    # Change arch to Debian format.
    debian_format = {
        "arm": "armhf",
        "x86_64": "amd64",
        "aarch64": "arm64",
        "loongarch64": "loong64",
        "powerpc64": "ppc64",
        "powerpc64le": "ppc64el",
    }
    if arch in debian_format.keys():
        arch = debian_format[arch]

    build_script = dist_profile["posix-build-script"]
    bin_dir = dist_profile["bin-dir"]

    # Build the package.
    colorize_output(sys.stdout, "white", "Building package ...\n")
    exec_command([os.path.abspath(os.path.join(build_script))])
    if not os.path.exists(bin_dir):
        colorize_output(sys.stdout, "red", "Path '%s' is not exist.\n" % bin_dir)
        return

    # Copy files.
    colorize_output(sys.stdout, "white", "Copying files ...\n")
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

    control_data = """Package: %s
Version: %s
Architecture: %s
Maintainer: %s
Description: %s
Essential: no
""" % (
        package,
        version,
        arch,
        maintainer,
        description,
    )

    if priority != "":
        control_data += "Priority: %s\n" % (priority)
    if installed_size != "":
        if installed_size == "auto":
            installed_size = get_dir_size(os.path.join(tempdir, "usr")) // 1024
        control_data += "Installed-Size: %s\n" % (installed_size)
    if homepage != "":
        control_data += "Homepage: %s\n" % (homepage)
    if section != "":
        control_data += "Section: %s\n" % (section)
    if depends != "":
        control_data += "Depends: %s\n" % (depends)
    if recommends != "":
        control_data += "Recommends: %s\n" % (recommends)
    if suggests != "":
        control_data += "Suggests: %s\n" % (suggests)
    if enhances != "":
        control_data += "Enhances: %s\n" % (enhances)
    if breaks != "":
        control_data += "Breaks: %s\n" % (breaks)
    if conflicts != "":
        control_data += "Conflicts: %s\n" % (conflicts)
    if pre_depends != "":
        control_data += "Pre-Depends: %s\n" % (pre_depends)
    with open(
        os.path.join(tempdir, "DEBIAN", "control"), mode="w", encoding="utf-8"
    ) as f:
        f.write(control_data)

    # Generate md5sums file.
    colorize_output(sys.stdout, "white", "Generating md5sums file ...\n")
    md5s = sum_files_md5(os.path.join(tempdir, "usr"))
    print(md5s)
    md5sums_data = ""
    for file in md5s.keys():
        md5sums_data += "%s  %s\n" % (md5s[file], os.path.relpath(file, tempdir))
    with open(
        os.path.join(tempdir, "DEBIAN", "md5sums"), mode="w", encoding="utf-8"
    ) as f:
        f.write(md5sums_data)

    # Copy preinst file.
    preinst_file = dist_profile.get("posix-pre-install-script", "")
    if preinst_file != "":
        colorize_output(sys.stdout, "white", "Copying preinst file ...\n")
        shutil.copy(preinst_file, os.path.join(tempdir, "DEBIAN", "preinst"))

    # Copy prerm file.
    prerm_file = dist_profile.get("posix-pre-remove-script", "")
    if prerm_file != "":
        colorize_output(sys.stdout, "white", "Copying prerm file ...\n")
        shutil.copy(prerm_file, os.path.join(tempdir, "DEBIAN", "prerm"))

    # Copy postinst file.
    postinst_file = dist_profile.get("posix-post-install-script", "")
    if postinst_file != "":
        colorize_output(sys.stdout, "white", "Copying postinst file ...\n")
        shutil.copy(postinst_file, os.path.join(tempdir, "DEBIAN", "postinst"))

    # Copy postrm file.
    postrm_file = dist_profile.get("posix-post-remove-script", "")
    if postrm_file != "":
        colorize_output(sys.stdout, "white", "Copying postrm file ...\n")
        shutil.copy(postrm_file, os.path.join(tempdir, "DEBIAN", "postrm"))

    # Build the package.
    colorize_output(sys.stdout, "white", "Building package ...\n")
    output_pkg_path = dist_profile["output-package-path"]
    output_pkg_dir = os.path.dirname(output_pkg_path)
    if not os.path.exists(output_pkg_dir):
        os.makedirs(output_pkg_dir)
    exec_command(["dpkg-deb", "--build", tempdir, output_pkg_path])

    colorize_output(sys.stdout, "green", "Package is built successfully.\n")


def make_distpkg(pkgtype, profile_file):
    """Make binary dist package.

    Args:
        pkgtype (str): Package type.
        profile_file (str): The path of the distribution profile.
    """

    dist_profile = FormatMap()
    with open(profile_file, mode="r", encoding="utf-8") as f:
        dist_profile = FormatMap.from_dict(json.load(f))

    colorize_output(
        sys.stdout,
        "white",
        "Making '%s' binary distribution package by profile '%s' ...\n"
        % (pkgtype, profile_file),
    )

    if pkgtype == "dpkg":
        make_deb(dist_profile)
    else:
        colorize_output(sys.stdout, "red", "Unknown package type '%s'.\n" % pkgtype)
        sys.exit(1)

    next_profile_path = dist_profile.get("next-profile", "")
    if next_profile_path != "":
        if os.path.abspath(next_profile_path) == os.path.abspath(profile_file):
            colorize_output(
                sys.stdout,
                "red",
                "Next profile is the same as current profile, ignored.\n",
            )
            sys.exit(1)
        next_profile = FormatMap()
        with open(next_profile_path, mode="r", encoding="utf-8") as f:
            next_profile = FormatMap.from_dict(json.load(f))
        make_distpkg(pkgtype, next_profile)


# Argument parser.
arg_parser = argparse.ArgumentParser(
    description="C++ Plus repository distributing, packaging and initialization utilities."
)
arg_parser.add_argument(
    "--root", default=".", help="The root directory of the repository."
)
subparsers = arg_parser.add_subparsers(dest="command", help="The command to execute.")
subparsers.add_parser("init", help="Initialize all required C++ Plus repository.")
subparsers.add_parser("deinit", help="Deinitialize all required C++ Plus repository.")
subparsers.add_parser("info", help="Print the package information.")
dist_parser = subparsers.add_parser(
    "dist", help="Make the source distribution package."
)
dist_parser.add_argument(
    "--distdir",
    default="$name-$version",
    help="The directory to save the distribution package, support variable: $name, $version.",
)

distpkg_parser = subparsers.add_parser("distpkg", help="Make the distribution package.")
distpkg_parser.add_argument("--type", default="", help="Make the Debian package.")

var_parser = arg_parser.add_argument_group("variable")
var_parser.add_argument(
    "--var",
    "-V",
    action="append",
    default=[],
    help="Set a variable, format: --var name=val",
)

VERSION_STRING = \
"""cppp-repoutils 0.1.0
Copyright (C) 2023 The C++ Plus Project.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
Written by ChenPi11.
"""
arg_parser.add_argument(
    "--version",
    "-v",
    action="store_true",
    default=False,
    help="Print the version of the program.",
)

# Main entry.


def main():
    """The main function of the repoutil module."""

    global profiles
    args = arg_parser.parse_args()
    os.chdir(os.path.abspath(args.root))

    profiles = load_profiles()

    # Set variables.
    push_variables("arch", get_arch())
    push_variables("name", profiles["name"])
    push_variables("root", os.path.abspath(os.curdir))
    push_variables("version", profiles["version"])

    if args.command == "init":
        setup_subpackages()
    elif args.command == "deinit":
        deinit_subpackages()
    elif args.command == "info":
        print_package_info()
    elif args.command == "dist":
        make_dist(
            format_string_with_variables(args.distdir)
        )
    elif args.command == "distpkg":
        if args.type == "":
            colorize_output(sys.stdout, "red", "Required options --type [dpkg]\n")
        else:
            make_distpkg(args.type, profiles["dist-profile"])
    elif args.version:
        colorize_output(sys.stdout, "white", VERSION_STRING)
    elif args.command is None:
        print_package_info()
    else:
        colorize_output(sys.stdout, "red", "Unknown command '%s'.\n" % args.command)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(3)
    except:
        print_error()
        sys.exit(1)
    finally:
        delete_all_temps()
