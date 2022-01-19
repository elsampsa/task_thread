#!/bin/bash
rm -f dist/*
rm -rf *.egg-info
python3 setup.py build sdist
