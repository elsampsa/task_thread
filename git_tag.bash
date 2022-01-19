#!/bin/bash

VERSION_MAJOR=0
VERSION_MINOR=5
VERSION_PATCH=3

# ver=\"$VERSION_MAJOR=0
ver=$VERSION_MAJOR"."$VERSION_MINOR"."$VERSION_PATCH

echo $ver

git tag -a $ver -m 'version $ver'
git push origin --tags

# # to delete the tag:
#
# git push --delete origin
#
