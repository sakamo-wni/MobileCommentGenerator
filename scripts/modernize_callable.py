#!/usr/bin/env python3
"""
CallableをPython 3.9+推奨のcollections.abc.Callableに変換するスクリプト
"""

import re
from pathlib import Path
from collections.abc import Callable as AbcCallable

def modernize_callable_imports(file_path: Path) -> int:
    """単一ファイルのCallableインポートを更新"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = 0
    
    # typing.Callableのインポートパターンを見つける
    patterns = [
        # from typing import Callable
        (r'from typing import (.*?)Callable(.*?)(?=\n|$)', 
         lambda m: process_typing_import(m.group(0), m.group(1), m.group(2))),
        # from typing import ..., Callable, ...
        (r'from typing import ([^;\n]*)', 
         lambda m: process_full_typing_import(m.group(0))),
    ]
    
    for pattern, processor in patterns:
        content = re.sub(pattern, processor, content)
    
    # collections.abc.Callableのインポートを追加（必要な場合）
    if 'Callable' in content and 'from collections.abc import' not in content:
        # typingインポートの後に追加
        typing_import = re.search(r'from typing import[^\n]+\n', content)
        if typing_import:
            insert_pos = typing_import.end()
            content = content[:insert_pos] + 'from collections.abc import Callable\n' + content[insert_pos:]
            changes += 1
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        changes += 1
    
    return changes


def process_typing_import(full_match: str, before: str, after: str) -> str:
    """typing importからCallableを除去"""
    # 前後の要素を取得
    before_items = [item.strip() for item in before.split(',') if item.strip()]
    after_items = [item.strip() for item in after.split(',') if item.strip() and item.strip() != '']
    
    all_items = before_items + after_items
    
    if not all_items:
        # Callableのみの場合、行を削除
        return ''
    else:
        # 他の要素がある場合
        return f"from typing import {', '.join(all_items)}"


def process_full_typing_import(full_match: str) -> str:
    """完全なtypingインポート文を処理"""
    if 'Callable' not in full_match:
        return full_match
    
    # インポートされている要素を抽出
    match = re.search(r'from typing import (.+)', full_match)
    if not match:
        return full_match
    
    imports = match.group(1)
    items = [item.strip() for item in imports.split(',')]
    
    # Callableを除去
    items = [item for item in items if 'Callable' not in item]
    
    if not items:
        return ''
    
    return f"from typing import {', '.join(items)}"


def main():
    """メイン処理"""
    print("Callableの型ヒントをcollections.abc.Callableに更新します...")
    
    # 対象ディレクトリ
    src_dir = Path(__file__).parent.parent / "src"
    tests_dir = Path(__file__).parent.parent / "tests"
    
    total_files = 0
    total_changes = 0
    
    for directory in [src_dir, tests_dir]:
        if not directory.exists():
            continue
            
        for py_file in directory.rglob("*.py"):
            # __pycache__を除外
            if "__pycache__" in str(py_file):
                continue
            
            changes = modernize_callable_imports(py_file)
            if changes > 0:
                print(f"✓ {py_file}: 更新しました")
                total_files += 1
                total_changes += changes
    
    print(f"\n完了: {total_files} ファイルを更新しました")


if __name__ == "__main__":
    main()