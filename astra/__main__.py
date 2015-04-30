import sys
import os
from importlib import import_module

# Determine the directory this file sits in.
astra_path = os.path.dirname(os.path.realpath(__file__))

# Determine what we are calling the astra package.
astra_pkg_name = os.path.basename(astra_path)

# Insert the directory above this into the path.
sys.path.insert(0, os.path.dirname(astra_path))

# Import the astra package
astra = import_module(astra_pkg_name)

astra.main()
