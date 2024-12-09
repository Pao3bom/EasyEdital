# Justfile
mb := "micromamba"

setup:
    cd explore && {{mb}} env create -f environment.yaml

test:
    - clear
    - rm -fr ./cache
    python3 test.py