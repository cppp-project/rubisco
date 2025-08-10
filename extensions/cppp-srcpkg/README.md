# cppp-srcpkg -- Rubisco source package builder

## How to use

**1. We provide a command '/srcdist' to archive sources.**

Usage:

`rubisco srcdist <srcdir> [--destination|-d <destdir>] [--archive-type|-t <type>] [--keep-source-directory|-k <true/false>] [--name-format|-f <format>]`

Arguments:

- `<srcdir>`: Path to the source directory. This is the directory that contains the source code of your project. Defaults to the current directory.

Options:

- `--destination` or `-d <destdir>`: (optional) Path to the destination directory where the source archive will be saved. Defaults to `dist/` in the project root.
- `--archive-type` or `-t <type>`: (optional) Archive type of the source distribution. Use '+' to make different archives. e.g. 'zip+tar.gz'. Use 'all' to select all supported types. Use 'none' to generate a directory instead of a archive. Defaults to 'all'.
- `--keep-source-directory` or `-k <true/false>`: (optional) Keep source directory. If `archive-type` is `none`, this option will be enabled. Defaults to `false`.
- `--name-format` or `-f <format>`: (optional) Package name format. Defaults to `<project-name>-<version>`.

## Build

```bash
rubisco build
```
