# cppp-repoutils
cppp-repoutils is a util package for C++ Plus repositories, it can only be used in C++ Plus source package development.

## Requirements
- Python 3.6 or later (mandatory)
- PyInstaller (for build)
- dpkg-deb (for build dpkg)

## Build
### If you not installed cppp-repoutils
```shell
python3 repoutils.py distpkg --type dpkg
```
Then you can find the package in `distpkg` directory.
### If you installed cppp-repoutils
```shell
cppp-repoutils distpkg --type dpkg
```
Then you can find the package in `distpkg` directory.
