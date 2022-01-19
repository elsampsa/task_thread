#!/bin/bash
read -p "Check that in dist/ there is only one .tar.gz package. Press enter to continue"
twine upload -r pypi dist/task_virtualthread*.tar.gz
