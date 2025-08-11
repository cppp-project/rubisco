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

"""Subpackage list utils."""

from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import TypeAlias

from rubisco.shared.api.uci import Tree
from rubisco.shared.api.variable import make_pretty

from subpackages.package import Package, SubpackageReference

__all__ = ["load_subpkg_list"]


@dataclass
class SubpackageRepr:
    """Subpackage representation."""

    name: str
    path: Path
    url: str | None
    branch: str | None
    is_fetched: bool
    cwd: Path

    is_duplicate: bool = False

    def __str__(self) -> str:
        """Return the string representation of the subpackage."""
        try:
            relpath = Path(self.path).relative_to(self.cwd)
        except ValueError:
            relpath = Path(self.path)
        path = make_pretty(relpath)
        res = ""

        if self.is_duplicate:
            res += f"⬅️ [cyan]{self.name}[/cyan]\t {path}"
        elif self.is_fetched:
            res += f"📂 [green]{self.name}[/green]\t"
            if self.url:
                res += (
                    f"[blue]{self.url}[/blue] [yellow]([/yellow][red]"
                    f"{self.branch}[/red][yellow])[/yellow] [blue]=>[/blue] "
                )
            res += f"[bold]{path}[/bold]"
        else:
            res += f"📦 [gray50]{self.name}[/gray50]\t"
            if self.url:
                res += (
                    f"[blue]{self.url}[/blue] [yellow]([/yellow][red]"
                    f"{self.branch}[/red][yellow])[/yellow] [blue]=>[/blue] "
                )
            res += f"[gray50]{path}[/gray50]"

        return res


_QueueItem: TypeAlias = tuple[Tree[SubpackageRepr], SubpackageReference]


def _load_subpkg_list(
    root: Tree[SubpackageRepr],
    pkg: SubpackageReference,
    loaded: set[str],
    cwd: Path,
) -> None:
    subpkg = Package(pkg.get_path())

    subpkgs_load_queue: Queue[_QueueItem] = Queue()
    for p in subpkg.subpackage_refs:
        path = p.get_path().resolve()
        uid = str(path) if p.exists() else p.url
        is_duplicate = uid in loaded
        subtree = Tree(
            SubpackageRepr(
                name=p.name,
                path=path,
                is_fetched=p.exists(),
                cwd=cwd,
                url=p.url,
                branch=p.branch,
                is_duplicate=is_duplicate,
            ),
        )
        root.add(subtree)
        if p.exists() and path not in loaded:
            loaded.add(uid)
        if not is_duplicate:
            subpkgs_load_queue.put((subtree, p))

    while not subpkgs_load_queue.empty():
        subtree, p = subpkgs_load_queue.get()
        _load_subpkg_list(subtree, p, loaded, cwd)


def load_subpkg_list(
    root: Tree[SubpackageRepr],
    pkg: Package,
    cwd: Path,
    *,
    recursive: bool,
) -> bool:
    """Load the subpackage list.

    Args:
        root (Tree[SubpackageRepr]): Tree root to load the subpackages into.
        pkg (Package): Package to load the subpackages from.
        cwd (Path | None): Current working directory. If provided, it will be
            used to resolve the subpackage paths.
        recursive (bool): Whether to load subpackages recursively.

    Returns:
        bool: Return True if no subpackages are found, False otherwise.

    """
    if not pkg.subpackages:
        return True

    loaded: set[str] = set()

    subpkgs_load_queue: Queue[_QueueItem] = Queue()
    for p in pkg.subpackage_refs:
        path = p.get_path().resolve()
        uid = str(path) if p.exists() else p.url
        subtree = Tree(
            SubpackageRepr(
                name=p.name,
                path=path,
                is_fetched=p.exists(),
                cwd=cwd,
                url=p.url,
                branch=p.branch,
                is_duplicate=uid in loaded,
            ),
        )
        root.add(subtree)
        loaded.add(uid)
        subpkgs_load_queue.put((subtree, p))

    if recursive:
        while not subpkgs_load_queue.empty():
            subtree, p = subpkgs_load_queue.get()
            if not p.exists():
                continue

            _load_subpkg_list(subtree, p, loaded, cwd)

    return False
