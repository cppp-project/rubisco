#!/usr/bin/sh

# Copyright (C) 2023 The C++ Plus Project.
# This file is part of the cppp-repoutils software.
#
# The cppp-repoutils software is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# The cppp-repoutils software is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with the cppp-repoutils software; see the file COPYING.
# If not, see <https://www.gnu.org/licenses/>.

# This script help to build the software.
# This script requires to run in the root directory of the repo.

# Usage: ./dist-tools/build.sh

colored_output() {
    if [ "$1" = "red" ]; then
        printf "\033[1;31m$2\033[0m $3\n"
    elif [ "$1" = "green" ]; then
        printf "\033[1;32m$2\033[0m $3\n"
    elif [ "$1" = "yellow" ]; then
        printf "\033[1;33m$2\033[0m $3\n"
    elif [ "$1" = "blue" ]; then
        printf "\033[1;34m$2\033[0m $3\n"
    elif [ "$1" = "white" ]; then
        printf "\033[1;37m$2\033[0m $3\n"
    else
        printf "$2 $3\n"
    fi
}

output_log() {
    timestamp=$(date +"%Y/%m/%d %H:%M:%S")
    colored_output "$1" "[$2] [$timestamp] $3"
}

# Check if we run this script in the root directory.
if [ ! -f "cppp-repo.json" ]; then
    output_log "red" "FATAL" "Please run this script in the root directory."
    exit 1
fi

# Make package
output_log "white" "INFO" "Making package..."

mkdir -p dist/bin
mkdir -p distpkg
cp src/cppp-repoutils.py dist/bin/cppp-repoutils

output_log "green" "SUCCESS" "Package made successfully."
exit 0
