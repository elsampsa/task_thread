#!/bin/bash
# clean python bytecode
find . -name "__pycache__" -exec rm -rf {} \;
find . -name "*.pyc" -exec rm -rf {} \;
# python autodoc clean:
find . -name "*.pickle" -exec rm -rf {} \;
