
from typing import Dict, Union, Any
from enum import Enum
import ast
import astor
import os

VariableValue = Union[str, bool, int, Dict[str, Any]]
VariableType = Enum('VariableType', ['String', 'Boolean', 'Number', 'JSON'])
Variable = Dict[str, Union[VariableValue, VariableType]]

class DVCLiteral:
    def __init__(self, value):
        self.value = value

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
        self.var_assignments = {}

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
    
    @staticmethod
    def literal(value):
        return DVCLiteral(value)

    @staticmethod
    def reduce_logical_expression(self, literal: DVCLiteral, expression: ast.Expression, operator: str) -> Union[DVCLiteral, ast.Expression]:
        if operator == 'and':
            return expression if literal.value else self.literal(False)
        elif operator == 'or':
            return self.literal(True) if literal.value else expression

    @staticmethod
    def reduce_binary_expression(literal_value: Union[int, str, bool], expression: ast.Expr, operator: str) -> Union[bool, None]:
        if not isinstance(expression, ast.Constant):
            return None

        if operator == '==':
            return literal_value == expression.value
        elif operator == '===':
            return literal_value is expression.value
    
    def get_assignment_value_if_set(self, expression):
        if isinstance(expression, ast.Name) and expression.id in self.var_assignments:
            return self.var_assignments[expression.id].value
        else:
            return expression

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
    
    def evaluate_expressions(self):
        def replace_node(node):
            updated_node = None
            if isinstance(node, ast.BoolOp):
                expression1 = self.get_assignment_value_if_set(self, node.values[0])
                expression2 = self.get_assignment_value_if_set(self, node.values[1])

                if isinstance(expression1, DVCLiteral):
                    updated_node = self.reduce_logical_expression(
                        self, expression1, expression2, node.op)
                elif isinstance(expression2, DVCLiteral):
                    updated_node = self.reduce_logical_expression(
                        self, expression2, expression1, node.op)

            elif isinstance(node, ast.BinOp):
                expression1 = self.get_assignment_value_if_set(self, node.left)
                expression2 = self.get_assignment_value_if_set(self, node.right)

                if isinstance(expression1, DVCLiteral):
                    updated_node = self.reduce_binary_expression(
                        expression1, expression2, node.op)
                elif isinstance(expression2, DVCLiteral):
                    updated_node = self.reduce_binary_expression(
                        expression2, expression1, node.op)

            elif isinstance(node, ast.UnaryOp) and isinstance(
                    node.op, ast.Not):
                node_argument = self.get_assignment_value_if_set(self, node.operand)

                if isinstance(node_argument, DVCLiteral):
                    literal_argument = node_argument
                    updated_node = ast.parse(
                        str(not literal_argument.value)).body[0].value

            if updated_node:
                engine.changed = True
                return updated_node

        engine = self
        ast_node = ast.parse(engine.code)
        for node in ast.walk(ast_node):
            if isinstance(node, ast.BoolOp) or isinstance(
                    node, ast.BinOp) or (isinstance(node, ast.UnaryOp)
                                         and isinstance(node.op, ast.Not)):
                updated_node = replace_node(node)
                if updated_node:
                    ast.copy_location(updated_node, node)
                    ast.fix_missing_locations(updated_node)

        engine.ast = ast_node

    def reduce_if_statements(self):

        def visit_if(node):
            test_value = self.get_assignment_value_if_set(self, node.test)

            if isinstance(test_value, ast.Constant):
                self.changed = True

                if test_value.value:
                    return node.body
                elif node.orelse is None:
                    return ast.Pass()
                else:
                    return node.orelse

        def flatten_blocks(node):
            new_body = []

            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    new_body.extend(flatten_blocks(stmt))
                else:
                    new_body.append(stmt)

            node.body = new_body

        tree = self.parser.parse(self.source)
        visitor = ast.NodeTransformer()

        visitor.visit(tree)
        visitor.visit(ast.fix_missing_locations(tree))

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                new_node = visit_if(node)

                if new_node is not None:
                    node.parent.body = new_node

        flatten_blocks(tree)
        return ast.unparse(tree)
    
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
