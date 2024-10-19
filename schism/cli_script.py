import os
import sys


def run():
    sys.path.append(os.getcwd())

    import schism.run
    schism.run.main(sys.argv[1:])

