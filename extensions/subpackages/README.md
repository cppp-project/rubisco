# subpackages -- Rubisco subpackage manager

## How to use

**1. We provide a command '/rubp/metadata' to get metadata about the Rubisco package.**

This command returns a JSON object for the RuBP.

**2. We provide a workflow to build the RuBP.**

```yaml
- name: Name of the step
  type: rubp-pack  # You must provide a unique identifier for the RuBP build step.
  srcdir: path/to/source  # (optional) Path to the project root directory, where the `repo.json` file is located. Defaults to the current directory.
  bindir: path/to/binary  # (optional) Path to the binary directory. Defaults to `.bindir` in the project root. All files in this directory will be included in the RuBP. But only `<module name>/`, `res/` and `rubisco.json` is allowed for a RuBP. The metadata will be generated automatically to `<bindir>/rubisco.json`.
  readme: path/to/README.md  # (optional) Path to the README file. Defaults to `README.md`/`README.txt`/`README`.
  license: path/to/LICENSE.txt  # (optional) Path to the license file. Defaults to `LICENSE.md`/`LICENSE.txt`/`LICENSE`/`COPYING`.
  distdir: path/to/dist  # (optional) RuBP output directory. Defaults to `dist/` in the project root.
  version: 1.0.0  # (optional) Version of the RuBP package. Defaults to `${{ project.version }}`.
```

**3. When generating metadata, we will get the following info from the `repo.json` file:**

- `name`: Name of the package.
- `version`: Version of the package.
- `description`: Description of the package.
- `maintainers`/`maintainer`: List of maintainers of the package or a single maintainer.
- `license`: License **name** of the package.
- `homepage`: Homepage of the package.
- `tags`: Optional. List of tags(keywords) for the package. Not git tags.
- `deps`: Optional. Dependencies of the package. You can specify the dependencies for unsupported languages. We support detecting dependencies for Python automatically. See the [Dependencies specification](#dependencies-specification) for more details.
- `latest-release`: The latest release link of the package. It must be a URL to the release RuBP file in a trusted website.

### Dependencies specification

You can specify the dependencies of the package in the `repo.json` file. The dependencies should be listed under the `deps` key. Each dependency should have the following structure:

```json
{
  "deps": [
    {
      "name": "dependency-name",
      "version": "1.0.0",
      "url": "https://example.com/dependency-home-page"
    }
  ]
}
```

The following languages are supported for automatic dependency detection:

- Python: Uses `requirements.txt` or `pyproject.toml` files to detect dependencies.

## Build

```bash
rubisco build
```

But we cannot use rubp-build to build rubp-build if it not installed. So we provide a script to build it:

```bash
./build_temp_rubp.sh
```

This script will make a temporary RuBP of rubp-build and install it automatically. After that, you can use `rubisco build` to build the RuBP.
