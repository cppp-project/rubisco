# subpackages -- Rubisco subpackage manager

## How to use

**1. You need to register subpackages in your repo config file.**

```json
{
  "subpackages": {
    "package name": {
      "path": "path/to/subpackage",  // Path to the subpackage directory.
      // You can also use "path": ["path1", "path2"] to specify alternative paths. If the first path does not exist, it will try the next one. If all paths do not exist, we will select the first one.
      "url": "user/repo@github",  // URL to the subpackage repository. SSH/HTTP(s)/GIT URL is supported.
      // You can also use "user/repo@host" to specify the host. This is recommended. Speedtest will run to select the fastest host. See your mirrorlist file.
      "branch": "main"  // Branch of the subpackage repository.
    }
  }
}
```

**2. We provide a command '/subpackages/fetch' to fetch subpackages.**

Options:

- `--protocol`/`-p`: Protocol to use for fetching subpackages. Supported protocols are `http`(means HTTP(s)) and `ssh`. Default is `http`.
- `--http`/`-H`: Use HTTP(s) protocol for fetching subpackages. Same as `--protocol https`.
- `--ssh`/`-S`: Use SSH protocol for fetching subpackages. Same as `--protocol ssh`.
- `--shallow [SHALLOW]`: Use shallow clone for fetching subpackages. If `SHALLOW` is `true`, it will use shallow clone. If `SHALLOW` is `false`, it will use full clone. Default is `true`.
- `--no-shallow`: Use full clone for fetching subpackages. Same as `--shallow false`.
- `--use-mirror [USE-MIRROR]`: Use mirror for fetching subpackages. If `USE-MIRROR` is `true`, it will use mirror. If `USE-MIRROR` is `false`, it will not use mirror and speedtest will not run. Default is `true`.
- `-m`: Same as `--use-mirror true`.
- `-M`: Same as `--use-mirror false`.

**2. We provide a command '/subpackages/list' to fetch subpackages.**

Options:

`--recursive [RECURSIVE]`: If `RECURSIVE` is `true`, it will list subpackages recursively. If `RECURSIVE` is `false`, it will not list subpackages recursively. Default is `true`.

If you run `rubisco subpackages list` in CLI, it will output the subpackages in a tree format like this:

```tree
📂 cppp .                                                                           // Root directory.
├── 📂 build-aux    <url of build-aux> (<branch>) => lib/build-aux                  // A fetched subpackage.
├── 📂 cppp-base    <url of cppp-base> (<branch>) => lib/cppp-base
│   ├── ⬅️ build-aux    lib/build-aux                                               // A alternative path for build-aux. It's not exists in the filesystem, but Rubisco found `build-aux` in `lib` directory. 
│   ├── ⬅️ cppp-reiconv   lib/cppp-reiconv
│   └── ⬅️ cppp-platform  lib/cppp-platform
├── 📂 cppp-reiconv  <url of cppp-reiconv> (<branch>) => lib/cppp-reiconv
│   └── ⬅️ build-aux      lib/build-aux
└── 📦 cppp-platform        <url of cppp-platform> (<branch>) => lib/cppp-platform // A not fetched subpackage reference.
```

In filesystem, it will look like this:

```tree
📂 .
├── 📂 lib
│   ├── 📂 build-aux
│   │   └── 📄 repo.json
│   ├── 📂 cppp-base
│   │   └── 📄 repo.json
│   └── 📂 cppp-reiconv
│       └── 📄 repo.json
└── 📄 repo.json
```

Confused? See cppp-base's subpackages.

```json
{
  "subpackages": {
    "build-aux": {
      "path": [
        "build-aux", // If we run fetch in `cppp/lib/cppp-base`, it will try to fetch build-aux in `cppp-base/build-aux`.
        "../build-aux" // But this path is found(cppp/lib/build-aux). And we run fetch in `cppp` so it will use this path.
      ],
      "url": "<url>",
      "branch": "main"
    },
    "cppp-reiconv": {
      "path": [
        "cppp-reiconv",
        "../cppp-reiconv"
      ],
      "url": "<url>",
      "branch": "main"
    },
    "cppp-platform": {
      "path": [
        "cppp-platform",
        "../cppp-platform"
      ],
      "url": "<url>",
      "branch": "main"
    }
  }
}
```

## Build

```bash
rubisco build
```
