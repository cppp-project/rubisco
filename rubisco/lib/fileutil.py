# -*- mode: python -*-
# vi: set ft=python :

# Copyright (C) 2024 The C++ Plus Project.
# This file is part of the cppp-rubisco.
#
# cppp-Rubisco is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# cppp-Rubisco is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""File utilities."""

from __future__ import annotations

import atexit
import fnmatch
import shutil
import sys
import tempfile
from typing import TYPE_CHECKING, Self

from rubisco.config import APP_NAME
from rubisco.lib.exceptions import (
    RUOSError,
    RUShellExecutionError,
    RUValueError,
)
from rubisco.lib.l10n import _
from rubisco.lib.log import logger
from rubisco.lib.pathlib import Path
from rubisco.lib.variable import format_str
from rubisco.shared.ktrigger import IKernelTrigger, call_ktrigger

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FunctionType, TracebackType

__all__ = [
    "TemporaryObject",
    "check_file_exists",
    "copy_recursive",
    "find_command",
    "glob_path",
    "human_readable_size",
    "resolve_path",
    "rm_recursive",
]


def check_file_exists(path: Path) -> None:
    """Check if the file exists. If exists, ask UCI to overwrite it.

    Args:
        path (Path): The path to check.

    Raises:
        AssertionError: If the file or directory exists and user choose to
            skip.

    """
    if path.exists():
        call_ktrigger(IKernelTrigger.file_exists, path=path)
        # UCI will raise an exception if user choose to skip.
        rm_recursive(path, strict=True)


def assert_rel_path(path: Path) -> None:
    """Assert that the path is a relative path.

    Args:
        path (Path): The path to assert.

    Raises:
        AssertionError: If the path is not a relative path.

    """
    if path.is_absolute():
        raise AssertionError(
            format_str(
                _(
                    "Absolute path '[underline]${{path}}[/underline]'"
                    " is not allowed.",
                ),
                fmt={"path": str(path)},
            ),
        )


def rm_recursive(
    path: Path,
    strict: bool = True,  # noqa: FBT001 FBT002
) -> None:
    """Remove a file or directory recursively.

    Args:
        path (Path): The path to remove.
        strict (bool): Raise an exception if error occurs.

    Raises:
        OSError: If strict is True and an error occurs.

    """
    assert_rel_path(path)

    path = path.absolute()

    def _onexc(  # pylint: disable=unused-argument
        func: FunctionType | None,  # noqa: ARG001
        path: str | Path,
        exc: BaseException,
    ) -> None:
        if not strict:
            call_ktrigger(
                IKernelTrigger.on_warning,
                message=format_str(
                    _(
                        "Error while removing '[underline]${{path}}"
                        "[/underline]': ${{error}}",
                    ),
                    fmt={"path": str(path), "error": str(exc)},
                ),
            )

    def _onerror(
        func: FunctionType,
        path: str | Path,
        exc_info: tuple[type, BaseException, TracebackType],
    ) -> None:
        return _onexc(func, path, exc_info[1])

    try:
        if path.is_dir() and not path.is_symlink():
            if sys.version_info <= (3, 12):
                shutil.rmtree(  # pylint: disable=deprecated-argument
                    path,
                    ignore_errors=not strict,
                    onerror=_onerror,  # type: ignore[arg-type]
                )
            else:
                shutil.rmtree(  # pylint: disable=unexpected-keyword-arg
                    path,
                    ignore_errors=not strict,
                    onexc=_onexc,  # type: ignore[arg-type]
                )
        else:
            path.unlink()
        logger.debug("Removed '%s'.", str(path))
    except OSError as exc:
        if strict:
            raise RUOSError(exc) from exc
        _onexc(None, path, exc)
        logger.warning("Failed to remove '%s'.", str(path), exc_info=exc)


def _match_path_only(pattern: str) -> bool:
    return "/" in pattern


def _ignore_patterns(
    patterns: list[str],
    start_dir: Path,
) -> Callable[[str, list[str]], set[str]]:
    """Return the function that can be used as `copytree()` ignore parameter.

    Patterns is a sequence of glob-style patterns
    that are used to exclude files

    """
    patterns = [pattern for pattern in patterns if pattern]

    def __ignore_patterns(strpath: str, strnames: list[str]) -> set[str]:
        path = Path(strpath).relative_to(start_dir)  # Always noexcept.
        names = [(path / Path(name)).as_posix() for name in strnames]
        ignored_names = []

        for pattern in patterns:
            if _match_path_only(pattern):
                res = fnmatch.filter(names, pattern)
                ignored_names.extend([Path(i).name for i in res])
            else:
                ignored_names.extend(fnmatch.filter(strnames, pattern))
        return set(ignored_names)

    return __ignore_patterns


def copy_recursive(  # pylint: disable=R0913, R0917 # noqa: PLR0913
    src: Path,
    dst: Path,
    strict: bool = False,  # noqa: FBT001 FBT002
    symlinks: bool = False,  # noqa: FBT001 FBT002
    exists_ok: bool = False,  # noqa: FBT001 FBT002
    ignore: list[str] | None = None,
) -> None:
    """Copy a file or directory recursively.

    Args:
        src (Path): The source path to copy.
        dst (Path): The destination path.
        strict (bool): Raise an exception if error occurs.
        symlinks (bool): Copy symlinks as symlinks.
        exists_ok (bool): Do not raise an exception if the destination exists.
        ignore (list[str] | None): The list of files to ignore.

    Raises:
        OSError: If strict is True and an error occurs.

    """
    if ignore is None:
        ignore = []

    src = src.absolute()
    dst = dst.absolute()
    try:
        if src.is_dir():
            shutil.copytree(
                src,
                dst,
                symlinks=symlinks,
                dirs_exist_ok=exists_ok,
                ignore=_ignore_patterns(ignore, src),
            )
        else:
            if dst.is_dir():
                dst = dst / src.name
            if dst.exists() and not exists_ok:
                raise FileExistsError(
                    format_str(
                        _(
                            "File '[underline]${{path}}[/underline]' "
                            "already exists.",
                        ),
                        fmt={"path": str(dst)},
                    ),
                )
            dst = Path(shutil.copy2(src, dst, follow_symlinks=not symlinks))
        logger.debug("Copied '%s' to '%s'.", str(src), str(dst))
    except OSError as exc:
        if strict:
            raise RUOSError(exc) from exc
        logger.warning(
            "Failed to copy '%s' to '%s'.",
            str(src),
            str(dst),
            exc_info=exc,
        )


tempdirs: set[Path] = set()


def new_tempdir(prefix: str = "", suffix: str = "") -> Path:
    """Create temporary directory but do not register it.

    Args:
        prefix (str): The prefix of the temporary directory
        suffix (str): The suffix of the temporary directory.

    Returns:
        str: The temporary directory.

    """
    return Path(
        tempfile.mkdtemp(
            suffix=suffix,
            prefix=prefix,
            dir=tempfile.gettempdir(),
        ),
    ).absolute()


def new_tempfile(prefix: str = "", suffix: str = "") -> Path:
    """Create temporary file but do not register it.

    Args:
        prefix (str): The prefix of the temporary file.
        suffix (str): The suffix of the temporary file.

    Returns:
        str: The temporary file.

    """
    return Path(
        tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=tempfile.gettempdir(),
        )[1],
    ).absolute()


class TemporaryObject:
    """A context manager for temporary files or directories."""

    # Type of the temporary object.
    TYPE_FILE: int = 0
    # Type of the temporary object.
    TYPE_DIRECTORY: int = 1
    # Auto-detecting the type of the temporary object. For register_tempobject.
    TYPE_AUTO: int = 2

    __path: Path
    __type: int
    __moved: bool = False

    def __init__(self, temp_type: int, path: Path) -> None:
        """Create a temporary object.

        Args:
            temp_type (int): The type of the temporary object.
                Can be TemporaryObject.TYPE_FILE or
                TemporaryObject.TYPE_DIRECTORY.
            path (Path): The path of the temporary object.
                We will register it for temporary later.

        """
        self.__type = temp_type
        self.__path = path
        tempdirs.add(self.__path)
        logger.debug("Registered temporary object '%s'.", str(self.__path))

    def __enter__(self) -> Self:
        """Enter the context manager.

        Returns:
            TemporaryObject: The temporary object path.

        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the context manager.

        Args:
            exc_type (type): The exception type.
            exc_value (Exception): The exception value.
            traceback (traceback): The traceback.

        """
        self.remove()

    def __str__(self) -> str:
        """Get the string representation of the temporary object.

        Returns:
            str: The string representation of the temporary object.

        """
        return str(self.path)

    def __repr__(self) -> str:
        """Get the string representation of the temporary object.

        Returns:
            str: The string representation of the temporary object.

        """
        return f"TemporaryDirectory({self.path!r})"

    def __hash__(self) -> int:
        """Get the hash of the temporary object.

        Returns:
            int: The hash of the temporary object.

        """
        return hash(self.path)

    def __eq__(self, obj: object) -> bool:
        """Compare the temporary object with another object.

        Args:
            obj (object): The object to compare.

        Returns:
            bool: True if the temporary object is equal to the object,
                False otherwise.

        """
        if not isinstance(obj, TemporaryObject):
            return False
        return self.path == obj.path

    def __ne__(self, obj: object) -> bool:
        """Compare the temporary object with another object.

        Args:
            obj (object): The object to compare.

        Returns:
            bool: True if the temporary object is not equal to the object,
                False otherwise.

        """
        return not self == obj

    @property
    def path(self) -> Path:
        """Get the temporary object path.

        Returns:
            Path: The temporary object path.

        """
        return self.__path

    @property
    def temp_type(self) -> int:
        """Get the temporary object type.

        Returns:
            int: The temporary object type.

        """
        return self.__type

    def is_file(self) -> bool:
        """Check if the temporary object is a file.

        Returns:
            bool: True if the temporary object is a file, False otherwise.

        """
        return self.path.is_file()

    def is_dir(self) -> bool:
        """Check if the temporary object is a object.

        Returns:
            bool: True if the temporary object is a object, False otherwise.

        """
        return self.path.is_dir()

    def remove(self) -> None:
        """Remove the temporary object."""
        if self.__moved:
            return
        if self.path.is_file():
            self.path.unlink()
        else:
            shutil.rmtree(self.path, ignore_errors=False)
        self.move()

    def move(self) -> Path:
        """Release the ownership of this temporary object.

        Returns:
            Path: The new location of the temporary object.

        """
        if self.__moved:
            return self.path
        try:
            tempdirs.remove(self.path)
            logger.debug("Unregistered temporary object '%s'.", str(self.path))
        except KeyError as exc:
            logger.warning(
                "Temporary object '%s' not found when unregistering.",
                str(self.path),
                exc_info=exc,
            )
        self.__moved = True
        return self.path

    @classmethod
    def new_file(cls, prefix: str = APP_NAME, suffix: str = "") -> Self:
        """Create a temporary file.

        Args:
            prefix (str, optional): Prefix of the temporary path.
                Defaults to APP_NAME.
            suffix (str, optional): Suffix of the temporary path.
                Defaults to "".

        Returns:
            TemporaryObject: The temporary file.

        """
        return cls(cls.TYPE_FILE, new_tempfile(prefix=prefix, suffix=suffix))

    @classmethod
    def new_directory(cls, prefix: str = APP_NAME, suffix: str = "") -> Self:
        """Create a temporary directory.

        Args:
            prefix (str, optional): Prefix of the temporary path.
                Defaults to APP_NAME.
            suffix (str, optional): Suffix of the temporary path.
                Defaults to "".

        Returns:
            TemporaryObject: The temporary directory.

        """
        return cls(
            cls.TYPE_DIRECTORY,
            new_tempdir(prefix=prefix, suffix=suffix),
        )

    @classmethod
    def register_tempobject(
        cls,
        path: Path,
        path_type: int = TYPE_AUTO,
    ) -> Self:
        """Register a file or a directory to a temporary object.

        Args:
            path (Path): The path of the object.
            path_type (int, optional): The type of the object.
                Can be TYPE_FILE, TYPE_DIRECTORY or TYPE_AUTO.
                If TYPE_FILE or TYPE_DIRECTORY is specified, create a temporary
                object with the specified type. If TYPE_AUTO is specified,
                auto-detect the type of the object. Defaults to TYPE_AUTO.

        Returns:
            TemporaryObject: Registered temporary object.

        """
        match path_type:
            case cls.TYPE_AUTO:
                return cls(
                    cls.TYPE_DIRECTORY if path.is_dir() else cls.TYPE_FILE,
                    path,
                )
            case cls.TYPE_FILE:
                if not path.exists():
                    path.touch()
                elif not path.is_file():
                    msg = format_str(
                        _("Invalid type: '${{path}}', expected file."),
                        fmt={"path": str(path)},
                    )
                    raise RUValueError(msg)
                return cls(cls.TYPE_FILE, path)
            case cls.TYPE_DIRECTORY:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                elif not path.is_dir():
                    msg = format_str(
                        _("Invalid type: '${{path}}', expected directory."),
                        fmt={"path": str(path)},
                    )
                    raise RUValueError(msg)
                return cls(cls.TYPE_DIRECTORY, path)
            case _:
                msg = "Invalid path type."
                raise ValueError(msg)

    @classmethod
    def cleanup(cls) -> None:
        """Clean up all temporary directories."""
        for tempdir in tempdirs:
            if tempdir.is_file():
                tempdir.unlink()
            else:
                shutil.rmtree(tempdir, ignore_errors=False)
            logger.debug("Unregistered temporary object '%s'.", str(tempdir))
        tempdirs.clear()


def resolve_path(
    path: Path,
    absolute_only: bool = True,  # noqa: FBT001 FBT002
) -> Path:
    """Resolve a path with globbing support.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool): Absolute path only instead of resolve.
            Defaults to True.

    Returns:
        Path: Resolved path.

    """
    res = path.expanduser().absolute()
    if absolute_only:
        return res
    return res.resolve()


def glob_path(
    path: Path,
    absolute_only: bool = True,  # noqa: FBT001 FBT002
) -> list[Path]:
    """Resolve a path and globbing it.

    Args:
        path (Path): Path to resolve.
        absolute_only (bool, optional): Absolute path only instead of resolve.
            Defaults to False.

    Returns:
        list[Path]: List of resolved paths.

    """
    return list(resolve_path(path, absolute_only).glob("*"))


def human_readable_size(size: float) -> str:
    """Convert size to human readable format.

    Args:
        size (float): The size to convert.

    Returns:
        str: The human readable size.

    """
    unit: str
    for unit_ in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]:
        unit = unit_
        if size < 1024.0:  # noqa: PLR2004
            break
        size /= 1024.0
    return f"{size:.2f}{unit}"


def find_command(
    cmd: str,
    strict: bool = True,  # noqa: FBT001 FBT002
) -> str | None:
    """Find the command in the system.

    Args:
        cmd (str): The command to find.
        strict (bool, optional): Raise an exception if the command is not
            found. Defaults to True.

    Returns:
        str: The command path.

    """
    logger.debug("Checking for command '%s' ...", cmd)

    res = shutil.which(cmd)

    logger.info(
        "Checking for command '%s' ... %s",
        cmd,
        res if res else "not found.",
    )

    if strict and res is None:
        raise RUShellExecutionError(
            format_str(_("Command '${{cmd}}' not found."), fmt={"cmd": cmd}),
            retcode=RUShellExecutionError.RETCODE_COMMAND_NOT_FOUND,
        )

    return res if res else None


# Register cleanup function.
atexit.register(TemporaryObject.cleanup)

if __name__ == "__main__":
    import pytest
    import rich

    # Test1: Basic usage.
    temp = TemporaryObject.new_file()
    rich.print("Created temporary file:", repr(temp))
    rich.print("tempdirs:", tempdirs)
    assert temp.is_file()  # noqa: S101
    assert not temp.is_dir()  # noqa: S101
    assert temp.temp_type == TemporaryObject.TYPE_FILE  # noqa: S101
    temp.remove()
    rich.print("Removed temporary file:", repr(temp))
    rich.print("tempdirs:", tempdirs)

    temp = TemporaryObject.new_directory()
    rich.print("Created temporary directory:", repr(temp))
    rich.print("tempdirs:", tempdirs)
    assert not temp.is_file()  # noqa: S101
    assert temp.is_dir()  # noqa: S101
    assert temp.temp_type == TemporaryObject.TYPE_DIRECTORY  # noqa: S101
    temp.remove()
    rich.print("Removed temporary directory:", repr(temp))
    rich.print("tempdirs:", tempdirs)

    # Test2: Context manager.
    with TemporaryObject.new_file() as temp:
        rich.print("Created temporary file:", repr(temp))
        rich.print("tempdirs:", tempdirs)
        assert temp.is_file()  # noqa: S101
        assert not temp.is_dir()  # noqa: S101
        assert temp.temp_type == TemporaryObject.TYPE_FILE  # noqa: S101
    rich.print("Removed temporary file:", repr(temp))
    rich.print("tempdirs:", tempdirs)

    with TemporaryObject.new_directory() as temp:
        rich.print("Created temporary directory:", repr(temp))
        rich.print("tempdirs:", tempdirs)
        assert not temp.is_file()  # noqa: S101
        assert temp.is_dir()  # noqa: S101
        assert temp.temp_type == TemporaryObject.TYPE_DIRECTORY  # noqa: S101
    rich.print("Removed temporary directory:", repr(temp))
    rich.print("tempdirs:", tempdirs)

    # Test3: Cleanup.
    temp1 = TemporaryObject.new_file()
    temp2 = TemporaryObject.new_directory()
    temp3 = TemporaryObject.new_file("-PREFIX-", "-SUFFIX-")
    temp4 = TemporaryObject.new_directory("-PREFIX-", "-SUFFIX-")
    rich.print("tempdirs:", tempdirs)
    TemporaryObject.cleanup()
    rich.print("Cleaned up temporary directories.")
    rich.print("tempdirs:", tempdirs)
    assert not temp1.path.exists()  # noqa: S101
    assert not temp2.path.exists()  # noqa: S101
    assert not temp3.path.exists()  # noqa: S101
    assert not temp4.path.exists()  # noqa: S101

    # Test4: Human readable size.
    assert human_readable_size(1023) == "1023.00B"  # noqa: S101
    assert human_readable_size(1024) == "1.00KiB"  # noqa: S101
    assert human_readable_size(1024**2) == "1.00MiB"  # noqa: S101
    assert human_readable_size(1024**3) == "1.00GiB"  # noqa: S101
    assert human_readable_size(1024**4) == "1.00TiB"  # noqa: S101
    assert human_readable_size(1024**5) == "1.00PiB"  # noqa: S101
    assert human_readable_size(1024**6) == "1.00EiB"  # noqa: S101
    assert human_readable_size(0) == "0.00B"  # noqa: S101

    # Test5: Find command.
    assert find_command("whoami") == shutil.which("whoami")  # noqa: S101

    with pytest.raises(RUShellExecutionError) as exc_:
        find_command("_Not_Exist_Command_", strict=True)
    assert (  # noqa: S101
        exc_.value.retcode == RUShellExecutionError.RETCODE_COMMAND_NOT_FOUND
    )
