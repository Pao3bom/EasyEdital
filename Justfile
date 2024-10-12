# Justfile
mb := "micromamba"

setup:
    cd explore && {{mb}} env create -f environment.yaml