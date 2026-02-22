import lks_quadgrab
import sys
import os
import unittest
import bpy

# Add the extension directory to sys.path
extension_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if extension_dir not in sys.path:
    sys.path.append(extension_dir)

# Register the extension
lks_quadgrab.register()

# Discover and run tests
test_dir = os.path.dirname(__file__)
suite = unittest.TestLoader().discover(test_dir)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Unregister the extension
lks_quadgrab.unregister()

# Exit with appropriate code
sys.exit(not result.wasSuccessful())
