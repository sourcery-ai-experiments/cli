import ast
import astor
import os
from typing import Dict

class PythonEngine:
    def __init__(self, filepath, variable: Dict, options: Dict):
        self.filepath = filepath
        self.output = 'console'
        self.ast = None
        self.varAssignments = {}
        self.changed = False
        self.fileRefactored = False

    @staticmethod
    def isDVCLiteral(node):
        return (
            node.type == 'Literal'
            and isinstance(node.value, bool)
            and node.raw.startswith('dvc(')
        )

    @staticmethod
    def isDVCObject(node):
        return (
            node.type == 'ObjectExpression'
            and any(
                prop.key.type == 'Identifier' and prop.key.name == 'dvc'
                for prop in node.properties
            )
        )
    
    def parseAST(self):
        try:
            parseOptions = {}
            with open(self.filepath, 'r') as file:
                source_code = file.read()
            self.ast = ast.parse(source_code, **parseOptions)
        except Exception as err:
            print(f"Error parsing file {self.filepath}")
            print(f"\t{err}")

    def printAST(self):
        try:
            code = astor.to_source(self.ast)
            if self.output == 'console':
                print(code)
            elif self.fileRefactored:
                with open(self.filepath, 'w') as file:
                    file.write(code)
        except Exception as err:
            print(f"Error occurred while recasting file {self.filepath}")
            print(f"\t{err}")

    def refactor(self):
        self.parseAST()
        if not self.ast:
            return

        self.changed = True
        iterations = 0

        # while self.changed and iterations < 10:
        #     self.changed = False
        #     iterations += 1

        #     self.replaceFeatureFlags()
        #     self.reduceObjects()
        #     self.varAssignments = self.getVariableMap()
        #     self.pruneVarReferences()
        #     self.evaluateExpressions()
        #     self.reduceIfStatements()
        #     if self.changed:
        #         self.fileRefactored = True

        self.printAST()
