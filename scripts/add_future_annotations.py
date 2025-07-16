#!/usr/bin/env python3
"""
__future__ import annotationsを追加するスクリプト

Python 3.10+では、from __future__ import annotationsを使用することで、
型ヒントの評価を遅延させ、より簡潔な記法が可能になります。
"""

import re
from pathlib import Path


def add_future_annotations(file_path: Path) -> bool:
    """単一ファイルに__future__ annotationsを追加"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # すでに存在する場合はスキップ
    if 'from __future__ import annotations' in content:
        return False
    
    # ファイルの先頭を解析
    lines = content.split('\n')
    
    # シバン、エンコーディング、docstringを見つける
    insert_index = 0
    in_docstring = False
    docstring_delimiter = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # シバンまたはエンコーディング宣言
        if i == 0 and (stripped.startswith('#!') or stripped.startswith('# -*- coding')):
            insert_index = i + 1
            continue
        
        # docstringの開始/終了を検出
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_delimiter = '"""' if stripped.startswith('"""') else "'''"
            if stripped.count(docstring_delimiter) >= 2:  # 単一行のdocstring
                in_docstring = False
                insert_index = i + 1
            continue
        
        if in_docstring and docstring_delimiter in stripped:
            in_docstring = False
            insert_index = i + 1
            continue
        
        # 最初のimport文またはコード行を見つけたら、その前に挿入
        if not in_docstring and stripped and not stripped.startswith('#'):
            insert_index = i
            break
    
    # __future__ importを追加
    future_import = "from __future__ import annotations\n"
    
    # 適切な位置に挿入
    if insert_index > 0 and lines[insert_index - 1].strip():
        # 前の行が空でない場合は空行を追加
        future_import = "\n" + future_import
    
    if insert_index < len(lines) and lines[insert_index].strip():
        # 次の行が空でない場合は空行を追加
        future_import = future_import + "\n"
    
    lines.insert(insert_index, future_import.rstrip())
    
    # ファイルを更新
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True


def main():
    """メイン処理"""
    print("__future__ import annotationsを追加します...")
    
    # 対象ディレクトリ
    src_dir = Path(__file__).parent.parent / "src"
    
    total_files = 0
    updated_files = 0
    
    if src_dir.exists():
        for py_file in src_dir.rglob("*.py"):
            # __pycache__を除外
            if "__pycache__" in str(py_file):
                continue
            
            # __init__.pyは除外（短いファイルが多いため）
            if py_file.name == "__init__.py":
                continue
            
            total_files += 1
            if add_future_annotations(py_file):
                print(f"✓ {py_file.relative_to(src_dir.parent)}")
                updated_files += 1
    
    print(f"\n完了: {updated_files}/{total_files} ファイルを更新しました")


if __name__ == "__main__":
    main()