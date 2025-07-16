#!/usr/bin/env python3
"""
型ヒント変換で発生した構文エラーを修正するスクリプト
"""

import os
import re
from pathlib import Path

# 除外するディレクトリ
EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'node_modules', '.mypy_cache', '.pytest_cache'}


def fix_syntax_errors(content: str) -> tuple[str, int]:
    """構文エラーを修正"""
    changes = 0
    
    # 連続するカンマを修正
    pattern = r'from typing import ([^,\n]+),\s*,\s*([^,\n]+)'
    new_content, count = re.subn(pattern, r'from typing import \1, \2', content)
    changes += count
    content = new_content
    
    # 先頭のカンマを修正
    pattern = r'from typing import\s*,\s*([^,\n]+)'
    new_content, count = re.subn(pattern, r'from typing import \1', content)
    changes += count
    content = new_content
    
    # 末尾のカンマを修正
    pattern = r'from typing import ([^,\n]+),\s*$'
    new_content, count = re.subn(pattern, r'from typing import \1', content, flags=re.MULTILINE)
    changes += count
    content = new_content
    
    # 空のimportを削除
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() == 'from typing import':
            changes += 1
            continue
        new_lines.append(line)
    
    return '\n'.join(new_lines), changes


def process_file(file_path: Path) -> int:
    """ファイルを処理"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        content, changes = fix_syntax_errors(content)
        
        if changes > 0:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ {file_path}: {changes} 箇所を修正")
        
        return changes
    
    except Exception as e:
        print(f"✗ {file_path}: エラー - {e}")
        return 0


def should_process_file(file_path: Path) -> bool:
    """ファイルを処理すべきか判定"""
    # 除外ディレクトリチェック
    for parent in file_path.parents:
        if parent.name in EXCLUDE_DIRS:
            return False
    
    # Pythonファイルかチェック
    return file_path.suffix == '.py'


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    tests_dir = project_root / 'tests'
    
    total_files = 0
    total_changes = 0
    
    print("型ヒントの構文エラーを修正します...")
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
    print(f"完了: {total_files} ファイル、{total_changes} 箇所を修正しました")


if __name__ == '__main__':
    main()