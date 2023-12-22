@echo off
rem Copyright (C) 2023 The C++ Plus Project.
rem This file is part of the cppp-repoutils.
rem
rem This file is free software: you can redistribute it and/or modify
rem it under the terms of the GNU General Public License as published
rem by the Free Software Foundation, either version 3 of the License,
rem or (at your option) any later version.
rem
rem This file is distributed in the hope that it will be useful,
rem but WITHOUT ANY WARRANTY; without even the implied warranty of
rem MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
rem GNU General Public License for more details.
rem
rem You should have received a copy of the GNU General Public License
rem along with this program.  If not, see <https://www.gnu.org/licenses/>.

rem Run C++ Plus compress utilities.
rem This program required py or python or python3 in PATH.

rem Usage:
rem   cppp-compress [command] [options]

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

set "SCRIPT_PATH=%~dp0\cppp-compress"
"%PYTHON_EXECUTABLE%" "%SCRIPT_PATH%" %*
set "ERRORLEVEL=%ERRORLEVEL%"
goto end

:error
set "ERRORLEVEL=1"

:end
endlocal & set "ERRORLEVEL=%ERRORLEVEL%"
exit /b %ERRORLEVEL%
