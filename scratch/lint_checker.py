import ast
import os
import sys

def analyze_file(filepath):
    print(f"Analyzing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"  SyntaxError: {e}")
        return

    imported_names = {}
    used_names = set()

    class Analyzer(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = (node.lineno, 'import')
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = (node.lineno, f'from {node.module}')
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            self.generic_visit(node)

        def visit_Attribute(self, node):
            # Check for attributes that might represent names
            self.generic_visit(node)

    analyzer = Analyzer()
    analyzer.visit(tree)

    # Builtin names to exclude
    builtins = set(dir(__builtins__))

    # Find unused imports
    unused_imports = []
    for name, (line, source) in imported_names.items():
        if name not in used_names:
            unused_imports.append((line, name, source))

    print("Unused imports:")
    for line, name, source in sorted(unused_imports):
        print(f"  Line {line}: '{name}' (imported via '{source}') is unused")

    # Find undefined names (very basic check)
    defined_names = set(builtins)
    for name in imported_names:
        defined_names.add(name)

    # Let's add class and function definitions to defined_names
    class DefFinder(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
        def visit_FunctionDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
            self.generic_visit(node)

    DefFinder().visit(tree)

    undefined = set()
    class UndefFinder(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load) and node.id not in defined_names:
                # check if it's a parameter in function or local var
                # For simplicity, we just check if it's in defined_names
                undefined.add((node.lineno, node.id))
            self.generic_visit(node)

    # UndefFinder is too naive for nested scopes, so let's just print unused imports for now.

if __name__ == '__main__':
    for f in sys.argv[1:]:
        analyze_file(f)
