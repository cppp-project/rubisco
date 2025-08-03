#!/bin/bash

# This is a temporary build script for building rubp-build extension.
# Building rubp-build needs rubp-build itself. So we need this script to build it first time.

mkdir -p .bindir
cp -r rubp_build .bindir

cat <<EOF > .bindir/rubisco.json
{
  "name": "rubp-build",
  "version": "0.0.1",
  "description": "",
  "maintainers": [],
  "versions": [],
  "license": "",
  "homepage": "",
  "tags": [],
  "deps": [],
  "latest_release": ""
}
EOF

cat <<EOF > .bindir/requirements.txt
pygit2 >= 1.18.1
tzlocal >= 5.3.1
packaging >= 25.0
EOF

rm -f rubp-build.zip
cd .bindir && zip -r ../rubp-build.zip ./*
cd .. || exit 1

rubisco ext uninstall rubp-build
rubisco ext install ./rubp-build.zip
