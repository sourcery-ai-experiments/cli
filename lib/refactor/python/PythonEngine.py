
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
        return isinstance(node, ast.Constant) and hasattr(node, '_created_by_dvc')

    @staticmethod
    def is_dvc_object(node):
        return isinstance(node, ast.Dict) and hasattr(node, '_created_by_dvc')

    @staticmethod
    def dvc_variable_object(variable: Variable) -> ast.Dict:
        """
        Build an AST Dict node from a DVC variable object
        """
        value = variable['value']
        if (variable['type'] == 'String'):
            value = '%s' % variable['value']
        elif (variable['type'] == 'Boolean'):
            value = False if variable['value'].lower() == 'false' else True
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
    def dvc_literal(node):
        node._created_by_dvc = True
        return node
    
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
            if (
                isinstance(node.func, ast.Attribute) and
                node.func.attr in self.sdk_methods and is_key_or_alias(node.args[1])
            ):
                return self.sdk_methods[node.func.attr]

        class NodeTraverse(ast.NodeTransformer):
            def visit_Call(self, node):
                variable_property = get_variable_property(node)
                if variable_property:
                    engine.changed = True
                    if (variable_property == 'variable'):
                        return engine.dvc_variable_object(engine.variable)
                return node
        
        self.ast = NodeTraverse().visit(self.ast)

    def reduce_objects(self):
        """
        Reduce object literals by replacing them with their corresponding variables,
        if they exist in the current scope.
        """
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            def visit_Attribute(self, node):
                # Replace DVC variable objects with indexed value, if applicable
                if (engine.is_dvc_object(node.value)):
                    for key, value in zip(node.value.keys, node.value.values):
                        if key.value == node.attr:
                            engine.changed = True
                            return engine.dvc_literal(value)
                return node

        NodeTraverse().visit(self.ast)

    def get_variable_map(self):
        """
        Build a map of variables assigned to a DVC literal or variable object
        Only booleans and variable objects should be replaced,
        other types will be referenced when evaluating conditionals
        """
        assignments = {}
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if engine.is_dvc_literal(node.value):
                            assignments[target.id] = {
                                'replace': isinstance(node.value.value, bool),
                                'value': node.value
                            }
                        elif engine.is_dvc_object(node.value):
                            assignments[target.id] = {
                                'replace': True,
                                'value': node.value
                            }
                return node

            def visit_Expr(self, node):
                if isinstance(node.value, ast.Assign):
                    for target in node.value.targets:
                        if isinstance(target, ast.Name):
                            if engine.is_dvc_literal(node.value.value):
                                assignments[target.id] = {
                                    'replace': isinstance(node.value.value.args[0].value, bool),
                                    'value': node.value.value.args[0].value
                                }
                            elif engine.is_dvc_object(node.value.value):
                                assignments[target.id] = {
                                    'replace': True,
                                    'value': node.value.value.args[0].keys
                                }
                return node

        NodeTraverse().visit(self.ast)
        return assignments

    def prune_variable_references(self):
        """
        Remove redundant variables by deleting declarations and replacing variable references
        """
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            # Remove variable declaration if necessary
            def visit_Assign(self, node):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name) and
                        target.id in engine.var_assignments and
                        engine.var_assignments[target.id]['replace'] == True
                    ):
                        engine.changed = True
                        return None
                return node

            # Replace node with variable value if necessary
            def visit_Name(self, node):
                if (
                    node.id in engine.var_assignments and
                    engine.var_assignments[node.id]['replace'] == True
                ):
                    engine.changed = True
                    return engine.var_assignments[node.id]['value']
                return node


        NodeTraverse().visit(self.ast)

    
    def evaluate_expressions(self):
        """
        Evaluate any expressions that can be reduced to a single value
        """
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            def visit_Expr(self, node):
                inner_node = ast.parse(node.value.args[0])

                if isinstance(inner_node, ast.BoolOp):
                    if isinstance(inner_node.values[0], ast.Constant):
                        value = engine.reduce_logical_expression(inner_node.values[0].value, inner_node.values[1], inner_node.op)
                        if value is not None:
                            engine.changed = True
                            return engine.literal(value)
                elif isinstance(inner_node, ast.BinOp):
                    if isinstance(inner_node.left, ast.Constant):
                        value = engine.reduce_binary_expression(inner_node.left.value, inner_node.right, inner_node.op)
                        if value is not None:
                            engine.changed = True
                            return engine.literal(value)
                    elif isinstance(inner_node.right, ast.Constant):
                        value = engine.reduce_binary_expression(inner_node.right.value, inner_node.left, inner_node.op)
                        if value is not None:
                            engine.changed = True
                            return engine.literal(value)
                elif isinstance(inner_node, ast.UnaryOp):
                    if isinstance(inner_node.operand, ast.Constant):
                        value = engine.reduce_unary_expression(inner_node.operand.value, inner_node.op)
                        if value is not None:
                            engine.changed = True
                            return engine.literal(value)
                return node

        NodeTraverse().visit(self.ast)

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

        tree = self.ast
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
            self.reduce_objects()
            self.var_assignments = self.get_variable_map()
            self.prune_variable_references()
            self.evaluate_expressions()
            # self.reduce_if_statements()
            if self.changed:
                self.file_refactored = True

        self.print_ast()
