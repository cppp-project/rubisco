# Repoutil variable system
## Usage
```shell
./repoutil.py --var name=value
```
In this example, the variable `name` will be set to `value`. The variable can be used in the **dist** profile file as `$name`. All of the string values in the **dist** profile supports variables.

## Default variables
The following variables are set by default:
- `arch`: The architecture of the system. This is the same as the output of `uname -m`.
- `name`: The name of the repository. This is the same as the `name` in `cppp-repo.json` profile file what you set.
- `root`: The root directory of the repository. This is the same as the output of `pwd`.
- `version`: The version of the repository. This is the same as the `version` in `cppp-repo.json` profile file what you set.
