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

"""Rubisco CommandEventFS Debugger CLI completer."""

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from rubisco.cli.cefs_dbg.lexer import KEYWORDS

if TYPE_CHECKING:
    from rubisco.cli.cefs_dbg.cli import RubiscoCEFSDebuggerCLI

__all__ = ["CEFSDebuggerCLICompleter"]


def get_left_longest_common_subsequence(
    text: str,
    candidates: Sequence[str],
) -> list[str]:
    """Get the left longest common subsequence of text and candidates.

    Args:
        text (str): The text to compare.
        candidates (list[str]): The candidates to compare.

    Returns:
        list[str]: The sorted candidates by left lcs length,
                  then by candidate length, then alphabetically.

    """
    if not text or not candidates:
        return []

    def lcs_length(a: str, b: str) -> int:
        """Calculate the length of the left-aligned lcs."""
        max_len = 0
        len_a, len_b = len(a), len(b)
        # Create a DP table initialized to 0
        dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]

        for i in range(1, len_a + 1):
            for j in range(1, len_b + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    max_len = max(max_len, dp[i][j])
                else:
                    dp[i][j] = 0  # Reset for left-aligned property
        return max_len

    # Calculate LCS length for each candidate
    candidates_with_lcs = [
        (candidate, lcs_length(text.lower(), candidate.lower()))
        for candidate in candidates
    ]

    # Filter out candidates with no match
    candidates_with_lcs = [x for x in candidates_with_lcs if x[1] > 0]

    # Sort by:
    # 1. LCS length (descending)
    # 2. Candidate length (ascending - prefer shorter matches when LCS is equal)
    # 3. Alphabetical order.
    candidates_with_lcs.sort(key=lambda x: (-x[1], len(x[0]), x[0].lower()))

    return [candidate for candidate, _ in candidates_with_lcs]


class CEFSDebuggerCLICompleter(Completer):
    """Rubisco CommandEventFS Debugger CLI completer."""

    cli_instance: "RubiscoCEFSDebuggerCLI"

    def __init__(self, cli_instance: "RubiscoCEFSDebuggerCLI") -> None:
        """Initialize the completer."""
        super().__init__()
        self.cli_instance = cli_instance

    def _keywords_completions(self) -> Iterable[Completion]:
        for keyword in KEYWORDS:
            yield Completion(keyword, start_position=0)

    def _keywords_completions_with_lcs(self, text: str) -> Iterable[Completion]:
        sorted_candidates = get_left_longest_common_subsequence(
            text,
            list(KEYWORDS),
        )
        for candidate in sorted_candidates:
            yield Completion(candidate, start_position=-len(text))

    def _arg_completions_list(self, cmd: str) -> list[str]:
        if cmd in {"cd", "ls"}:
            return [str(x.name) for x in self.cli_instance.cwd.list_dirs()]
        if cmd == "cat":
            return [str(x.name) for x in self.cli_instance.cwd.list_files()]
        if cmd == "stat":
            return [str(x.name) for x in self.cli_instance.cwd.iterpath()]
        if cmd == "help":
            return list(KEYWORDS)
        return []

    def _arg_completions(self, cmd: str) -> Iterable[Completion]:
        for comp in self._arg_completions_list(cmd):
            yield Completion(str(comp), start_position=0)

    def _arg_completions_with_lcs(
        self,
        cmd: str,
        text: str,
    ) -> Iterable[Completion]:
        sorted_candidates = get_left_longest_common_subsequence(
            text,
            self._arg_completions_list(cmd),
        )
        for candidate in sorted_candidates:
            yield Completion(candidate, start_position=-len(text))

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,  # noqa: ARG002
    ) -> Iterable[Completion]:
        """Get completions for the given document.

        Args:
            document (Document): The document to complete.
            complete_event (CompleteEvent): The complete event.

        Returns:
            Iterable[Completion]: The completions.

        Yields:
            Completion: The completion.

        """
        if not document.text_before_cursor:
            yield from self._keywords_completions()
            return

        args = document.text_before_cursor.split()

        text = args[-1]
        arg_count = len(args)
        if arg_count == 1:
            if " " not in document.text_before_cursor:
                yield from self._keywords_completions_with_lcs(text)
                return
            cmd = text.strip()
            yield from self._arg_completions(cmd)
            return

        if arg_count == 2:  # noqa: PLR2004
            cmd = args[0]
            yield from self._arg_completions_with_lcs(cmd, text)
            return
