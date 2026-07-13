import ast
import sys

def lint_file(filepath):
    print(f"\nLinting {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"Failed to parse {filepath}: {e}")
        return

    # Track definitions and usages
    imported_names = {}  # name -> (lineno, source)
    global_names = set()
    used_names = set()
    
    class ScopeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.scopes = [{}] # list of dicts (name -> type)
            self.undefined = []
            self.unused_locals = []

        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = (node.lineno, 'import')
                self.scopes[-1][name] = 'import'
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = (node.lineno, f'from {node.module}')
                self.scopes[-1][name] = 'import'
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.scopes[-1][node.name] = 'class'
            # New scope for class body
            self.scopes.append({})
            self.generic_visit(node)
            self.scopes.pop()

        def visit_FunctionDef(self, node):
            self.scopes[-1][node.name] = 'function'
            # New scope for function body
            self.scopes.append({})
            # Add parameters to scope
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                self.scopes[-1][arg.arg] = 'param'
            if node.args.vararg:
                self.scopes[-1][node.args.vararg.arg] = 'param'
            if node.args.kwarg:
                self.scopes[-1][node.args.kwarg.arg] = 'param'
            
            self.generic_visit(node)
            # Check unused locals in this scope
            scope = self.scopes.pop()
            for name, ntype in scope.items():
                if ntype in ('local', 'param') and name not in used_names and not name.startswith('_'):
                    self.unused_locals.append((node.lineno, name, ntype))

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
                # Check if defined in any scope
                defined = False
                for scope in reversed(self.scopes):
                    if node.id in scope:
                        defined = True
                        break
                # Builtins
                if not defined and node.id in dir(__builtins__):
                    defined = True
                if not defined and node.id in ('pygame', 'sys', 'random', 'math', 'config'): # module imports
                    defined = True
                if not defined:
                    self.undefined.append((node.lineno, node.id))
            elif isinstance(node.ctx, ast.Store):
                # Define in current scope
                self.scopes[-1][node.id] = 'local'
            self.generic_visit(node)

    visitor = ScopeVisitor()
    visitor.visit(tree)

    print("Unused Imports:")
    unused_imp_count = 0
    for name, (line, source) in imported_names.items():
        if name not in used_names:
            print(f"  Line {line}: Unused import '{name}'")
            unused_imp_count += 1

    print("Undefined Names:")
    undef_count = 0
    for line, name in sorted(set(visitor.undefined)):
        print(f"  Line {line}: Undefined name '{name}'")
        undef_count += 1

    print("Unused Locals/Params:")
    unused_local_count = 0
    for line, name, ntype in sorted(visitor.unused_locals):
        print(f"  Line {line}: Unused {ntype} '{name}'")
        unused_local_count += 1

if __name__ == "__main__":
    for path in sys.argv[1:]:
        lint_file(path)
