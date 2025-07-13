#\!/usr/bin/env python3
import os
import re
from collections import defaultdict

def extract_imports(filepath):
    """ファイルからインポートを抽出"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # from ... import パターン
        from_imports = re.findall(r'from\s+([\w\.]+)\s+import', content)
        # import パターン
        direct_imports = re.findall(r'^import\s+([\w\.]+)', content, re.MULTILINE)
        
        imports.extend(from_imports)
        imports.extend(direct_imports)
        
        # 相対インポートを絶対パスに変換
        module_path = filepath.replace('/', '.').replace('.py', '')
        resolved_imports = []
        
        for imp in imports:
            if imp.startswith('.'):
                # 相対インポートの処理
                level = len(imp) - len(imp.lstrip('.'))
                parts = module_path.split('.')
                if level < len(parts):
                    base = '.'.join(parts[:-level])
                    relative_part = imp.lstrip('.')
                    if relative_part:
                        resolved = f"{base}.{relative_part}"
                    else:
                        resolved = base
                    resolved_imports.append(resolved)
            else:
                resolved_imports.append(imp)
        
        return resolved_imports
    except Exception as e:
        return []

def find_circular_imports(root_dir):
    """循環インポートを検出"""
    import_graph = defaultdict(set)
    file_map = {}
    
    # すべてのPythonファイルを収集
    for root, dirs, files in os.walk(root_dir):
        # 不要なディレクトリをスキップ
        if '__pycache__' in root or '.egg-info' in root or 'node_modules' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                module_name = filepath.replace(root_dir + '/', '').replace('/', '.').replace('.py', '')
                file_map[module_name] = filepath
                
                imports = extract_imports(filepath)
                for imp in imports:
                    # プロジェクト内のインポートのみ
                    if imp.startswith('src') or imp.startswith('app'):
                        import_graph[module_name].add(imp)
    
    # 循環を検出
    def find_cycle(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in import_graph.get(node, []):
            if neighbor not in visited:
                cycle = find_cycle(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # 循環を発見
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        path.pop()
        rec_stack.remove(node)
        return None
    
    cycles = []
    visited = set()
    
    for node in import_graph:
        if node not in visited:
            rec_stack = set()
            path = []
            cycle = find_cycle(node, visited, rec_stack, path)
            if cycle:
                cycles.append(cycle)
    
    return cycles

# プロジェクトルートから検索
cycles = find_circular_imports('.')

if cycles:
    print("循環インポートが検出されました:")
    for i, cycle in enumerate(cycles, 1):
        print(f"\n循環 {i}:")
        for j in range(len(cycle) - 1):
            print(f"  {cycle[j]} → {cycle[j+1]}")
else:
    print("循環インポートは検出されませんでした。")
