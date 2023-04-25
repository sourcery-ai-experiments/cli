import ast
import astor
import os
from typing import Dict, Union
from enum import Enum

VariableValue = Union[str, bool, int, Dict[str, any]]
VariableType = Enum('VariableType', ['String', 'Boolean', 'Number', 'JSON'])
Variable = Dict[str, Union[VariableValue, VariableType]]

class PythonEngine:
    sdk_methods = {
        'variable': 'variable'
    }

    def __init__(self, filepath, variable: Dict, options: Dict):
        self.filepath = filepath
        self.variable = variable
        self.output = options['output'] if 'output' in options else 'console'
        self.aliases = options['aliases'] if 'aliases' in options else {}
        self.ast = None
        self.var_assignments = {}
        self.changed = False
        self.file_refactored = False

    @staticmethod
    def is_dvc_literal(node):
        return (
            node.type == 'Literal'
            and isinstance(node.value, bool)
            and node.raw.startswith('dvc(')
        )

    @staticmethod
    def is_dvc_object(node):
        return (
            node.type == 'ObjectExpression'
            and any(
                prop.key.type == 'Identifier' and prop.key.name == 'dvc'
                for prop in node.properties
            )
        )

    @staticmethod
    def dvc_variable_object(variable: Variable) -> ast.Dict:
        """
        Build an AST Dict node from a DVC variable object
        """
        value = variable['value']
        if (variable['type'] == 'String'):
            value = '%s' % variable['value']
        elif (variable['type'] == 'Boolean'):
            value = variable['value'] == False if 'false' else True
        elif (variable['type'] == 'Number'):
            value = float(variable['value'])

        dict = ast.Dict(
            keys=[
                ast.Constant(value='key'),
                ast.Constant(value='value'),
                ast.Constant(value='defaultValue'),
                ast.Constant(value='isDefaulted')
            ],
            values=[
                ast.Constant(value=variable['key']),
                ast.Constant(value=value),
                ast.Constant(value=value),
                ast.Constant(value=True)
            ]
        )
        dict._created_by_dvc = True

        return dict

    def replace_feature_flags(self):
        """
        Replace any DVC SDK variable methods with a static variable object
        """
        engine = self
        def is_key_or_alias(arg):
            if isinstance(arg, ast.Constant):
                return arg.value == self.variable['key']
            else:
                is_key = arg.id == self.variable['key']
                is_alias = arg.id in self.aliases
                return is_key or is_alias

        def get_variable_property(node):
            if not isinstance(node, ast.Call):
                return None
            if (
                isinstance(node.func, ast.Attribute) and
                node.func.attr in self.sdk_methods and is_key_or_alias(node.args[1])
            ):
                return self.sdk_methods[node.func.attr]

        class ReplaceVariable(ast.NodeTransformer):
            def generic_visit(self, node):
                # Need to call super() in any case to visit child nodes of the current one.
                super().generic_visit(node)
                variable_property = get_variable_property(node)
                if variable_property:
                    self.changed = True
                    if (variable_property == 'variable'):
                        return engine.dvc_variable_object(engine.variable)
                return node
        
        self.ast = ReplaceVariable().visit(self.ast)
    
    def parse_ast(self):
        try:
            parseOptions = {}
            with open(self.filepath, 'r') as file:
                source_code = file.read()
            self.ast = ast.parse(source_code, **parseOptions)
        except Exception as err:
            print(f"Error parsing file {self.filepath}")
            print(f"\t{err}")

    def print_ast(self):
        try:
            code = astor.to_source(self.ast)
            if self.output == 'console':
                print(code)
            elif self.file_refactored:
                with open(self.filepath, 'w') as file:
                    file.write(code)
        except Exception as err:
            print(f"Error occurred while recasting file {self.filepath}")
            print(f"\t{err}")

    def refactor(self):
        self.parse_ast()
        if not self.ast:
            return

        self.changed = True
        iterations = 0

        while self.changed and iterations < 10:
            self.changed = False
            iterations += 1

            self.replace_feature_flags()
        #     self.reduceObjects()
        #     self.var_assignments = self.getVariableMap()
        #     self.pruneVarReferences()
        #     self.evaluateExpressions()
        #     self.reduceIfStatements()
            if self.changed:
                self.file_refactored = True

        self.print_ast()
