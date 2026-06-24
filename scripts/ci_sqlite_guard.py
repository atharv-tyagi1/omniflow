import ast
import os
from pathlib import Path
import sys

def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
        
    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return False
        
    found_sqlite = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if 'sqlite' in name.name.lower():
                    print(f"FAIL: {filepath} imports {name.name}")
                    found_sqlite = True
        elif isinstance(node, ast.ImportFrom):
            if node.module and 'sqlite' in node.module.lower():
                print(f"FAIL: {filepath} imports from {node.module}")
                found_sqlite = True
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if 'omniflow.db' in node.value or ('sqlite' in node.value and 'dialect' not in node.value and 'sqlite_where' not in node.value):
                # We specifically check for sqlite dialect strings or db filenames
                if node.value.startswith('sqlite') or node.value == 'omniflow.db':
                    print(f"FAIL: {filepath} contains sqlite string literal: {node.value}")
                    found_sqlite = True
    return found_sqlite

def run_checks():
    target_dir = Path("backend/app")
    failed = False
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                if check_file(filepath):
                    failed = True
                    
    if failed:
        print("SQLite Guard Check: FAILED. Production code must not reference SQLite.")
        sys.exit(1)
    else:
        print("SQLite Guard Check: PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    run_checks()
