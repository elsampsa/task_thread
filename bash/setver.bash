#!/bin/bash
if [ $# -ne 3 ]; then
  echo "Give major minor patch"
  exit
fi
# mod python files: TODO: you might need to edit this
find -name "*.py" -exec sed -i -r "s/@version .*/@version $1.$2.$3 /g" {} \;
find -name "*.py" -exec sed -i -r "s/\* Version  \:.*/\* Version  \: $1.$2.$3/g" {} \;
# # grab into these
# @version 0.1
# * Version  : 0.1

fs="setup.py docs/*"
for f in $fs
do
  find $f -exec sed -i -r "s/version = '.*'/version = '$1.$2.$3'/g" {} \;
  find $f -exec sed -i -r "s/release = '.*'/version = '$1.$2.$3'/g" {} \;
done

export version_file=$(find -name "version.py")

fs="git_tag.bash git_rm_tag.bash "$version_file
for f in $fs
do
  # mod version numbers in git_tag.bash
  sed -i -r "s/VERSION_MAJOR=.*/VERSION_MAJOR=$1/g" $f
  sed -i -r "s/VERSION_MINOR=.*/VERSION_MINOR=$2/g" $f
  sed -i -r "s/VERSION_PATCH=.*/VERSION_PATCH=$3/g" $f
done

echo
echo Updating docs
echo
cd docs
./compile.bash
cd ..
