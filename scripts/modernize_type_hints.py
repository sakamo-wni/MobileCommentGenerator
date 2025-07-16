#!/usr/bin/env python3
"""
型ヒントをPython 3.9+のモダンな記法に更新するスクリプト

古い記法: from typing import Dict, List, Optional, Union, Tuple, Set
新しい記法: dict, list, | None, |, tuple, set
"""

import os
import re
from pathlib import Path
# 型ヒントは新しい構文を使用

# 変換マッピング
TYPE_MAPPINGS = {
    # TypedDictを含まないようにDict前に負の先読みアサーションを追加
    r'\b(?<!Type)Dict\[([^]]+)\]': r'dict[\1]',
    r'\bList\[([^]]+)\]': r'list[\1]',
    r'\bTuple\[([^]]+)\]': r'tuple[\1]',
    r'\bSet\[([^]]+)\]': r'set[\1]',
    r'\bOptional\[([^]]+)\]': r'\1 | None',
    r'\bUnion\[([^,]+),\s*([^]]+)\]': r'\1 | \2',
}

# インポート文の変換パターン
IMPORT_PATTERNS = [
    (r'from typing import (.*)Dict(.*)', r'from typing import \1\2'),
    (r'from typing import (.*)List(.*)', r'from typing import \1\2'),
    (r'from typing import (.*)Tuple(.*)', r'from typing import \1\2'),
    (r'from typing import (.*)Set(.*)', r'from typing import \1\2'),
    (r'from typing import (.*)Optional(.*)', r'from typing import \1\2'),
    (r'from typing import (.*)Union(.*)', r'from typing import \1\2'),
]

# 除外するディレクトリ
EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'node_modules', '.mypy_cache', '.pytest_cache'}


def should_process_file(file_path: Path) -> bool:
    """ファイルを処理すべきか判定"""
    # 除外ディレクトリチェック
    for parent in file_path.parents:
        if parent.name in EXCLUDE_DIRS:
            return False
    
    # Pythonファイルかチェック
    return file_path.suffix == '.py'


def update_imports(content: str) -> tuple[str, int]:
    """import文を更新"""
    changes = 0
    
    # まず必要なimportを収集
    typing_imports = []
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('from typing import'):
            # typing importから旧型を除去
            original_line = line
            for old_pattern, new_pattern in IMPORT_PATTERNS:
                line = re.sub(old_pattern, new_pattern, line)
            
            # 空のimportを削除
            if line.strip() == 'from typing import':
                changes += 1
                continue
            
            # カンマだけ残った場合の処理
            line = re.sub(r',\s*,', ',', line)
            line = re.sub(r',\s*\)', ')', line)
            line = re.sub(r'\(\s*,', '(', line)
            
            if line != original_line:
                changes += 1
        
        new_lines.append(line)
    
    return '\n'.join(new_lines), changes


def update_type_hints(content: str) -> tuple[str, int]:
    """型ヒントを更新"""
    changes = 0
    
    for old_pattern, new_pattern in TYPE_MAPPINGS.items():
        new_content, count = re.subn(old_pattern, new_pattern, content)
        changes += count
        content = new_content
    
    return content, changes


def process_file(file_path: Path) -> int:
    """ファイルを処理"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # import文を更新
        content, import_changes = update_imports(content)
        
        # 型ヒントを更新
        content, hint_changes = update_type_hints(content)
        
        total_changes = import_changes + hint_changes
        
        if total_changes > 0:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ {file_path}: {total_changes} 箇所を更新")
        
        return total_changes
    
    except Exception as e:
        print(f"✗ {file_path}: エラー - {e}")
        return 0


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    tests_dir = project_root / 'tests'
    
    total_files = 0
    total_changes = 0
    
    print("型ヒントのモダン化を開始します...")
    print(f"対象ディレクトリ: {src_dir}, {tests_dir}")
    print()
    
    # srcディレクトリとtestsディレクトリを処理
    for directory in [src_dir, tests_dir]:
        if not directory.exists():
            continue
            
        for file_path in directory.rglob('*.py'):
            if should_process_file(file_path):
                changes = process_file(file_path)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
    
    print()
    print(f"完了: {total_files} ファイル、{total_changes} 箇所を更新しました")
    
    # 特に更新が多いUIモジュールの統計
    ui_files = list((src_dir / 'ui').rglob('*.py')) if (src_dir / 'ui').exists() else []
    if ui_files:
        print(f"\n※ UIモジュール: {len(ui_files)} ファイル中で更新")


if __name__ == '__main__':
    main()