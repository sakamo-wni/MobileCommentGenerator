#\!/usr/bin/env python3
import ast
import os

def analyze_python_file(filepath):
    """Pythonファイルを解析して未使用のインポートを検出"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # インポートされた名前を収集
        imported_names = set()
        import_statements = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name.split('.')[0])
                    import_statements.append((alias.name, name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
                    import_statements.append((f"{node.module}.{alias.name}", name, node.lineno))
        
        # 使用されている名前を収集
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # モジュール名も含める
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # 未使用のインポートを検出
        unused_imports = []
        for full_name, imported_name, lineno in import_statements:
            if imported_name not in used_names:
                # __all__ に含まれているか確認
                if '__all__' in content and f'"{imported_name}"' in content:
                    continue
                unused_imports.append((full_name, imported_name, lineno))
        
        return unused_imports
    except Exception as e:
        return None

# 主要なファイルをチェック
files_to_check = [
    'app.py',
    'api_server.py',
    'app_controller.py',
    'src/config/config.py',
    'src/controllers/comment_generation_controller.py',
    'src/workflows/comment_generation_workflow.py'
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        unused = analyze_python_file(filepath)
        if unused:
            print(f"\n{filepath}:")
            for full_name, name, lineno in unused:
                print(f"  Line {lineno}: '{name}' (from {full_name})")
