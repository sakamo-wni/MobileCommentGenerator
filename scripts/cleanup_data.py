#!/usr/bin/env python3
"""データクリーンアップスクリプト

定期的に実行してforecast_cacheとgeneration_historyのクリーンアップを行います。

使用例:
    # 統計情報のみ表示（ドライラン）
    python scripts/cleanup_data.py --dry-run
    
    # 実際にクリーンアップを実行
    python scripts/cleanup_data.py
    
    # 保持日数を指定してクリーンアップ
    python scripts/cleanup_data.py --retention-days 14
    
    # cronでの定期実行例（毎日午前3時）
    0 3 * * * cd /path/to/project && python scripts/cleanup_data.py >> logs/cleanup.log 2>&1
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.data_manager import DataManager
from src.utils.exceptions import FileOperationError

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='天気コメント生成データのクリーンアップ')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際の削除は行わず、統計情報のみ表示'
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        help='forecast_cacheの保持日数（デフォルトは設定ファイルの値）'
    )
    parser.add_argument(
        '--skip-forecast',
        action='store_true',
        help='forecast_cacheのクリーンアップをスキップ'
    )
    parser.add_argument(
        '--skip-history',
        action='store_true',
        help='generation_historyのアーカイブをスキップ'
    )
    parser.add_argument(
        '--clean-archives',
        action='store_true',
        help='古いアーカイブファイルも削除'
    )
    parser.add_argument(
        '--keep-archives',
        type=int,
        default=5,
        help='保持するアーカイブファイル数（デフォルト: 5）'
    )
    
    args = parser.parse_args()
    
    try:
        manager = DataManager()
        
        # 現在の統計情報を表示
        logger.info("=== 現在のデータ統計 ===")
        stats = manager.get_data_statistics()
        logger.info(json.dumps(stats, indent=2, ensure_ascii=False))
        
        if args.dry_run:
            logger.info("\n=== ドライランモード（実際の削除は行いません） ===")
            
            # forecast_cacheの情報
            if not args.skip_forecast:
                retention_days = args.retention_days or manager.forecast_retention_days
                logger.info(f"forecast_cache: {retention_days}日より古いデータを削除対象とします")
                logger.info(f"  現在のファイル数: {stats['forecast_cache'].get('file_count', 0)}")
                logger.info(f"  合計行数: {stats['forecast_cache'].get('total_rows', 0)}")
            
            # generation_historyの情報
            if not args.skip_history:
                history_stats = stats.get('generation_history', {})
                if history_stats.get('needs_archive'):
                    logger.info(f"generation_history: アーカイブが必要です")
                    logger.info(f"  現在のサイズ: {history_stats.get('size_mb', 0):.2f}MB")
                    logger.info(f"  閾値: {manager.history_max_size_mb}MB")
                else:
                    logger.info(f"generation_history: アーカイブは不要です")
                    logger.info(f"  現在のサイズ: {history_stats.get('size_mb', 0):.2f}MB")
            
            # アーカイブの情報
            if args.clean_archives:
                archive_stats = stats.get('archives', {})
                logger.info(f"アーカイブ: {archive_stats.get('count', 0)}個のファイル")
                if archive_stats.get('count', 0) > args.keep_archives:
                    logger.info(f"  削除対象: {archive_stats.get('count', 0) - args.keep_archives}個")
            
            return
        
        # 実際のクリーンアップを実行
        logger.info("\n=== クリーンアップを開始 ===")
        
        # forecast_cacheのクリーンアップ
        if not args.skip_forecast:
            logger.info("\n--- forecast_cacheのクリーンアップ ---")
            try:
                result = manager.clean_forecast_cache(args.retention_days)
                logger.info(f"完了: {result}")
            except FileOperationError as e:
                logger.error(f"forecast_cacheのクリーンアップに失敗: {e}")
        
        # generation_historyのアーカイブ
        if not args.skip_history:
            logger.info("\n--- generation_historyのアーカイブ ---")
            try:
                result = manager.archive_generation_history()
                logger.info(f"完了: {result}")
            except FileOperationError as e:
                logger.error(f"generation_historyのアーカイブに失敗: {e}")
        
        # 古いアーカイブの削除
        if args.clean_archives:
            logger.info("\n--- 古いアーカイブの削除 ---")
            try:
                result = manager.cleanup_old_archives(args.keep_archives)
                logger.info(f"完了: {result}")
            except FileOperationError as e:
                logger.error(f"アーカイブの削除に失敗: {e}")
        
        # 最終的な統計情報を表示
        logger.info("\n=== クリーンアップ後のデータ統計 ===")
        final_stats = manager.get_data_statistics()
        logger.info(json.dumps(final_stats, indent=2, ensure_ascii=False))
        
        logger.info("\n=== クリーンアップ完了 ===")
        
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {type(e).__name__} - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()