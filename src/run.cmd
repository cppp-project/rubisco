@echo off
rem Copyright (C) 2023 The C++ Plus Project.
rem This file is part of the cppp-reiconv library.
rem
rem The cppp-reiconv library is free software; you can redistribute it
rem and/or modify it under the terms of the GNU Lesser General Public
rem License as published by the Free Software Foundation; either version 3
rem of the License, or (at your option) any later version.
rem
rem The cppp-reiconv library is distributed in the hope that it will be
rem useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
rem MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
rem Lesser General Public License for more details.
rem
rem You should have received a copy of the GNU Lesser General Public
rem License along with the cppp-reiconv library; see the file COPYING.
rem If not, see <https://www.gnu.org/licenses/>.

rem Run C++ Plus repository utilities.
rem This program required py, python, python3 in PATH.

rem Usage:
rem   cppp-repoutils [command] [options]

setlocal
set PYTHON_EXECUTABLE=python

rem Check python is valid.
%PYTHON_EXECUTABLE% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_EXECUTABLE=python3
    %PYTHON_EXECUTABLE% --version >nul 2>&1
    if errorlevel 1 (
        set PYTHON_EXECUTABLE=py
        %PYTHON_EXECUTABLE% --version >nul 2>&1
        if errorlevel 1 (
            echo Error: python is not found. >&2
            echo Please install python in PATH. >&2
            goto error
        )
    )
)

set "SCRIPT_PATH=%~dp0\cppp-repoutils"
"%PYTHON_EXECUTABLE%" "%SCRIPT_PATH%" %*
set "ERRORLEVEL=%ERRORLEVEL%"
goto end

:error
set "ERRORLEVEL=1"

:end
endlocal & set "ERRORLEVEL=%ERRORLEVEL%"
exit /b %ERRORLEVEL%
