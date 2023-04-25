import sys
import json
from PythonEngine import PythonEngine

filename, filename_to_refactor, variable_string, options_string = sys.argv
variable = json.loads(variable_string)
options = json.loads(options_string)
PythonEngine(filename_to_refactor, variable, options).refactor()