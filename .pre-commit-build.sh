#!/bin/bash
# Pre-build script to ensure Python 3.12 is used
python --version
if [[ $(python --version 2>&1) != *"3.12"* ]]; then
    echo "ERROR: Python 3.12 required, but found: $(python --version)"
    exit 1
fi

