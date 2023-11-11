#!/usr/bin/env pwsh

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
# This script requires PyInstaller program and C/C++ compiler in the PATH.
# This script requires to run in the root directory of the repo.

# Usage: ./dist-tools/build.ps1

function colored_output {
    param (
        [Parameter(Mandatory=$true)][System.String]$color,
        [Parameter(Mandatory=$true)][string]$message
    )
    Write-Host $message -ForegroundColor $color
}

function output_log {
    param (
        [Parameter(Mandatory=$true)][string]$color,
        [Parameter(Mandatory=$true)][string]$level,
        [Parameter(Mandatory=$true)][string]$message
    )
    $timestamp = Get-Date -Format "yyyy/MM/dd HH:mm:ss"
    colored_output $color "[$level] [$timestamp] $message"
}

# Check PyInstaller program.
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    output_log Red FATAL "PyInstaller program not found in PATH."
    exit 1
}
# Check if we run this script in the root directory.
if (-not (Test-Path "repoutils.spec")) {
    output_log Red FATAL "Please run this script in the root directory."
    exit 1
}
# Make package
output_log White INFO "Making package..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

pyinstaller --clean --noconfirm repoutils.spec
if ($LASTEXITCODE -ne 0) {
    output_log Red FATAL "Failed to make package."
    exit 1
}

New-Item -Path "dist/bin" -ItemType Directory -Force | Out-Null
Move-Item -Path "dist/cppp-repoutils*" -Destination "dist/bin" -Force | Out-Null

output_log Green SUCCESS "Package made successfully."
exit 0
