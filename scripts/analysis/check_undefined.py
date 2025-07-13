#\!/usr/bin/env python3
import ast
import os

def check_undefined_names(filepath):
    """未定義の名前の使用をチェック"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # 定義された名前を収集
        defined_names = set()
        # ビルトインも追加
        defined_names.update(['True', 'False', 'None', 'self', '__name__', '__all__'])
        
        # インポートされた名前
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    defined_names.add(name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        # ワイルドカードインポートは解析困難
                        return None
                    name = alias.asname if alias.asname else alias.name
                    defined_names.add(name)
            elif isinstance(node, ast.FunctionDef):
                defined_names.add(node.name)
                # 引数も追加
                for arg in node.args.args:
                    defined_names.add(arg.arg)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
        
        # 使用されている名前をチェック
        undefined_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in defined_names and not node.id.startswith('__'):
                    # グローバル関数など一般的なものは除外
                    if node.id not in ['print', 'len', 'str', 'int', 'float', 'dict', 
                                       'list', 'set', 'tuple', 'open', 'range', 'enumerate',
                                       'isinstance', 'hasattr', 'getattr', 'setattr']:
                        undefined_names.append((node.id, node.lineno))
        
        return undefined_names
    except Exception as e:
        return None

# 主要ファイルをチェック
files = [
    'api_server.py',
    'src/workflows/comment_generation_workflow.py',
    'src/nodes/weather_forecast_node.py'
]

for filepath in files:
    if os.path.exists(filepath):
        undefined = check_undefined_names(filepath)
        if undefined:
            print(f"\n{filepath}:")
            seen = set()
            for name, lineno in undefined:
                if name not in seen:
                    print(f"  Line {lineno}: '{name}' is not defined")
                    seen.add(name)
