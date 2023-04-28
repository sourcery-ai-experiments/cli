
from typing import Dict, Union, Any
from enum import Enum
import ast
import ast_comments

VariableValue = Union[str, bool, int, Dict[str, Any]]
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
        elif (variable['type'] == 'JSON'):
            value = ast.parse(str(variable['value'])).body[0].value

        ast_value = value if variable['type'] == 'JSON' else ast.Constant(value)
        ast_value._created_by_dvc = True

        dict = ast.Dict(
            keys=[
                ast.Constant('key'),
                ast.Constant('value'),
                ast.Constant('defaultValue'),
                ast.Constant('isDefaulted')
            ],
            values=[
                ast.Constant(variable['key']),
                ast_value,
                ast_value,
                ast.Constant(True)
            ]
        )
        dict._created_by_dvc = True

        return dict

    @staticmethod
    def dvc_literal(node):
        node._created_by_dvc = True
        return node

    @staticmethod
    def reduce_logical_expression(left_value: ast.Expr, right_value: ast.Expr, operator: str) -> Union[ast.Constant, None]:
        """
        Accepts two values and an operator, and returns a single value if the expression can be reduced.
        Returns None if the expression cannot be reduced.
        """
        # Determine which value, if any, was created by DVC
        dvc_literal, expression = None, None
        if PythonEngine.is_dvc_literal(left_value):
            dvc_literal = left_value
            expression = right_value
        elif PythonEngine.is_dvc_literal(right_value):
            dvc_literal = right_value
            expression = left_value

        if dvc_literal is None:
            return None

        if operator == 'And()':
            return expression if dvc_literal.value else ast.Constant(False)
        elif operator == 'Or()':
            return ast.Constant(True) if dvc_literal.value else expression
        
        try:
            if isinstance(expression, ast.Constant):
                if operator == 'Eq()':
                    return ast.Constant(left_value.value == right_value.value)
                elif operator == 'Lt()':
                    return ast.Constant(left_value.value < right_value.value)
                elif operator == 'LtE()':
                    return ast.Constant(left_value.value <= right_value.value)
                elif operator == 'Gt()':
                    return ast.Constant(left_value.value > right_value.value)
                elif operator == 'GtE()':
                    return ast.Constant(left_value.value >= right_value.value)
        except:
            return None
    
    def get_assignment_value_if_set(self, expression):
        if isinstance(expression, ast.Name) and expression.id in self.var_assignments:
            return self.var_assignments[expression.id]['value']
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
        Replace DVC variable objects with indexed value, if applicable
        ex. `{ value: 'foo' }.value` would be replaced with `'foo'`
        """
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            def handle_attribute(self, node, attribute):
                # Replace DVC variable objects with indexed value, if applicable
                if (engine.is_dvc_object(node.value)):
                    for key, value in zip(node.value.keys, node.value.values):
                        if key.value == attribute:
                            engine.changed = True
                            return engine.dvc_literal(value)
                super().generic_visit(node)
                return node

            def visit_Attribute(self, node):
                return self.handle_attribute(node, node.attr)

            def visit_Subscript(self, node):
                return self.handle_attribute(node, node.slice.value)

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
                super().generic_visit(node)
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
                super().generic_visit(node)
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
        Remove variable declarations and replace variable references
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
                super().generic_visit(node)
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
            def visit_BoolOp(self, node):
                left_value = engine.get_assignment_value_if_set(node.values[0])
                right_value = engine.get_assignment_value_if_set(node.values[1])

                reduced_value = engine.reduce_logical_expression(left_value, right_value, ast.dump(node.op))
                if reduced_value is not None:
                    engine.changed = True
                    # In case expressions contains more than 2 values, only replace first 2
                    node.values = [reduced_value] + node.values[2:]

                if len(node.values) == 1:
                    return engine.dvc_literal(node.values[0])
                return node

            def visit_Compare(self, node):
                left_value = engine.get_assignment_value_if_set(node.left)
                right_value = engine.get_assignment_value_if_set(node.comparators[0])

                reduced_value = engine.reduce_logical_expression(left_value, right_value, ast.dump(node.ops[0]))
                if reduced_value is not None:
                    engine.changed = True
                    return engine.dvc_literal(reduced_value)
                return node

            # Unary operators (ex. not)
            def visit_UnaryOp(self, node):
                value = engine.get_assignment_value_if_set(node.operand)
                if engine.is_dvc_literal(value):
                    engine.changed = True
                    return engine.dvc_literal(ast.Constant(not value.value))
                return node

        NodeTraverse().visit(self.ast)

    def reduce_if_statements(self):
        """
        Reduce if statements that are always true/false
        """
        engine = self
        class NodeTraverse(ast.NodeTransformer):
            def handle_if(self, node):
                value = None
                if engine.is_dvc_literal(node.test):
                    value = node.test.value
                # Non-boolean values are referenced, not replaced. Check if they are assigned to a value
                elif isinstance(node.test, ast.Name) and node.test.id in engine.var_assignments:
                    value = engine.var_assignments[node.test.id]['value']

                if value is not None:
                    engine.changed = True
                    return node.body if value else node.orelse
                return node

            def visit_If(self, node):
                return self.handle_if(node)

            def visit_IfExp(self, node):
                return self.handle_if(node)

        NodeTraverse().visit(self.ast)
    
    def parse_ast(self):
        try:
            with open(self.filepath, 'r') as file:
                source_code = file.read()
            self.ast = ast_comments.parse(source_code)

        except Exception as err:
            print(f"Error parsing file {self.filepath}")
            print(f"\t{err}")

    def print_ast(self):
        try:
            code = ast_comments.unparse(self.ast)

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
            self.reduce_if_statements()
            if self.changed:
                self.file_refactored = True

        self.print_ast()
