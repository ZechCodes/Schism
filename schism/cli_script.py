"""This module is intended solely to enable the schism command script that is configured in pyproject.toml."""
import os
import sys


def run():
    sys.path.append(os.getcwd())

    import schism.run
    schism.run.main(sys.argv[1:])

