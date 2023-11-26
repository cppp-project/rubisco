# cppp-repoutils
cppp-repoutils is a util package for C++ Plus repositories, it can only be used in C++ Plus source package development.

## Requirements
- Python2 or Python3 or later (mandatory)
- dpkg-deb (for build dpkg)

## Build
### If you not installed cppp-repoutils
```shell
python repoutils.py distpkg --type dpkg
```
Then you can find the package in `distpkg` directory.
### If you installed cppp-repoutils
```shell
cppp-repoutils distpkg --type dpkg
```
Then you can find the package in `distpkg` directory.
