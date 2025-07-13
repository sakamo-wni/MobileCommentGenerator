#\!/usr/bin/env python3
import ast
import os

def find_dead_code(filepath):
    """定義されているが使用されていない関数・クラスを検出"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # 定義された関数とクラスを収集
        defined_functions = {}
        defined_classes = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # プライベート関数（_で始まる）とマジックメソッドは除外
                if not node.name.startswith('_'):
                    defined_functions[node.name] = node.lineno
            elif isinstance(node, ast.ClassDef):
                defined_classes[node.name] = node.lineno
        
        # 使用されている名前を収集
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)
        
        # __all__に含まれている名前も使用済みとする
        if '__all__' in content:
            all_match = ast.literal_eval(content.split('__all__')[1].split('=')[1].split('\n')[0].strip())
            if isinstance(all_match, list):
                used_names.update(all_match)
        
        # 未使用のものを検出
        unused_functions = []
        unused_classes = []
        
        for func_name, lineno in defined_functions.items():
            if func_name not in used_names:
                # main関数やテスト関数は除外
                if func_name not in ['main', 'test', 'run_streamlit_app']:
                    unused_functions.append((func_name, lineno))
        
        for class_name, lineno in defined_classes.items():
            if class_name not in used_names:
                unused_classes.append((class_name, lineno))
        
        return unused_functions, unused_classes
    except Exception as e:
        return [], []

# 主要ファイルをチェック
files_to_check = [
    'app.py',
    'api_server.py',
    'src/workflows/comment_generation_workflow.py',
    'src/nodes/weather_forecast_node.py',
    'src/utils/error_handler.py',
    'src/config/config.py'
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        unused_funcs, unused_classes = find_dead_code(filepath)
        if unused_funcs or unused_classes:
            print(f"\n{filepath}:")
            if unused_funcs:
                print("  未使用の関数:")
                for name, lineno in unused_funcs:
                    print(f"    Line {lineno}: {name}()")
            if unused_classes:
                print("  未使用のクラス:")
                for name, lineno in unused_classes:
                    print(f"    Line {lineno}: class {name}")
