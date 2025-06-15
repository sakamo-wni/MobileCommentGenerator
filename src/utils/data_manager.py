"""データ管理ユーティリティ

forecast_cacheやgeneration_historyなどのデータファイルの管理を行います。
古いデータの削除、アーカイブ、圧縮などの機能を提供します。
"""

import json
import logging
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import csv

from src.config.config_loader import ConfigLoader
from src.utils.exceptions import FileOperationError, DataError

logger = logging.getLogger(__name__)


class DataManager:
    """データファイルの管理を行うクラス"""
    
    def __init__(self):
        # S3設定から管理設定を読み込み
        config = ConfigLoader.load_config("s3_config.yaml")
        self.data_config = config.get("data_management", {})
        
        # デフォルト値
        self.forecast_retention_days = self.data_config.get("forecast_cache_retention_days", 30)
        self.history_max_size_mb = self.data_config.get("generation_history_max_size_mb", 100)
        self.history_archive_days = self.data_config.get("generation_history_archive_interval_days", 7)
        
        # ディレクトリパス
        self.forecast_cache_dir = Path("data/forecast_cache")
        self.generation_history_file = Path("data/generation_history.json")
        self.archive_dir = Path("data/archive")
        
        # アーカイブディレクトリを作成
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_forecast_cache(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """古いforecast_cacheデータを削除
        
        Args:
            retention_days: 保持日数（指定しない場合は設定値を使用）
            
        Returns:
            削除結果の統計情報
        """
        retention_days = retention_days or self.forecast_retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted_files = []
        deleted_rows = 0
        processed_files = 0
        
        logger.info(f"Cleaning forecast cache older than {retention_days} days...")
        
        try:
            for csv_file in self.forecast_cache_dir.glob("*.csv"):
                processed_files += 1
                
                # CSVファイルを読み込み
                rows_to_keep = []
                rows_deleted = 0
                
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        headers = reader.fieldnames
                        
                        for row in reader:
                            # target_datetime列から日時を解析
                            try:
                                target_dt_str = row.get('target_datetime', '')
                                if target_dt_str:
                                    target_dt = datetime.fromisoformat(target_dt_str.replace('Z', '+00:00'))
                                    
                                    # 古いデータは削除
                                    if target_dt < cutoff_date:
                                        rows_deleted += 1
                                        deleted_rows += 1
                                    else:
                                        rows_to_keep.append(row)
                                else:
                                    # 日時が無い行は保持
                                    rows_to_keep.append(row)
                            except (ValueError, KeyError) as e:
                                # 解析できない行は保持
                                logger.debug(f"Failed to parse datetime in {csv_file}: {e}")
                                rows_to_keep.append(row)
                    
                    # ファイルを書き戻す（削除された行がある場合のみ）
                    if rows_deleted > 0:
                        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=headers)
                            writer.writeheader()
                            writer.writerows(rows_to_keep)
                        
                        logger.info(f"Cleaned {csv_file.name}: {rows_deleted} rows deleted")
                    
                    # ファイルが空になった場合は削除
                    if len(rows_to_keep) == 0:
                        csv_file.unlink()
                        deleted_files.append(csv_file.name)
                        logger.info(f"Deleted empty file: {csv_file.name}")
                        
                except (IOError, OSError) as e:
                    logger.error(f"I/O error processing {csv_file}: {type(e).__name__} - {e}")
                except csv.Error as e:
                    logger.error(f"CSV error processing {csv_file}: {type(e).__name__} - {e}")
                    
        except (IOError, OSError) as e:
            logger.error(f"I/O error cleaning forecast cache: {type(e).__name__} - {e}")
            raise FileOperationError("Failed to clean forecast cache") from e
        
        result = {
            "processed_files": processed_files,
            "deleted_files": len(deleted_files),
            "deleted_rows": deleted_rows,
            "retention_days": retention_days
        }
        
        logger.info(f"Forecast cache cleanup complete: {result}")
        return result
    
    def archive_generation_history(self) -> Dict[str, Any]:
        """generation_historyをアーカイブして圧縮
        
        Returns:
            アーカイブ結果の統計情報
        """
        if not self.generation_history_file.exists():
            logger.warning("Generation history file not found")
            return {"status": "not_found"}
        
        try:
            # ファイルサイズを確認
            file_size_mb = self.generation_history_file.stat().st_size / (1024 * 1024)
            
            if file_size_mb < self.history_max_size_mb:
                logger.info(f"Generation history size ({file_size_mb:.2f}MB) is below threshold ({self.history_max_size_mb}MB)")
                return {
                    "status": "skipped",
                    "file_size_mb": file_size_mb,
                    "threshold_mb": self.history_max_size_mb
                }
            
            # アーカイブファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"generation_history_{timestamp}.json.gz"
            archive_path = self.archive_dir / archive_name
            
            # JSONファイルを読み込み、古いエントリと新しいエントリを分離
            with open(self.generation_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cutoff_date = datetime.now() - timedelta(days=self.history_archive_days)
            old_entries = []
            new_entries = []
            
            for entry in data:
                try:
                    # タイムスタンプを解析
                    timestamp_str = entry.get('timestamp', '')
                    if timestamp_str:
                        entry_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        if entry_date < cutoff_date:
                            old_entries.append(entry)
                        else:
                            new_entries.append(entry)
                    else:
                        # タイムスタンプがない場合は新しいエントリとして扱う
                        new_entries.append(entry)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse timestamp: {e}")
                    new_entries.append(entry)
            
            # 古いエントリをアーカイブ
            if old_entries:
                with gzip.open(archive_path, 'wt', encoding='utf-8') as gz:
                    json.dump(old_entries, gz, ensure_ascii=False, indent=2)
                
                logger.info(f"Archived {len(old_entries)} entries to {archive_name}")
                
                # 新しいエントリのみを元のファイルに保存
                with open(self.generation_history_file, 'w', encoding='utf-8') as f:
                    json.dump(new_entries, f, ensure_ascii=False, indent=2)
                
                # 新しいファイルサイズ
                new_file_size_mb = self.generation_history_file.stat().st_size / (1024 * 1024)
                
                result = {
                    "status": "archived",
                    "archive_file": archive_name,
                    "archived_entries": len(old_entries),
                    "remaining_entries": len(new_entries),
                    "original_size_mb": file_size_mb,
                    "new_size_mb": new_file_size_mb,
                    "compression_ratio": (file_size_mb - new_file_size_mb) / file_size_mb * 100 if file_size_mb > 0 else 0
                }
            else:
                result = {
                    "status": "no_old_entries",
                    "total_entries": len(data),
                    "file_size_mb": file_size_mb
                }
            
            logger.info(f"Generation history archive complete: {result}")
            return result
            
        except (IOError, OSError) as e:
            logger.error(f"I/O error archiving generation history: {type(e).__name__} - {e}")
            raise FileOperationError("Failed to archive generation history") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON error archiving generation history: {type(e).__name__} - {e}")
            raise DataError("Invalid JSON format in generation history") from e
    
    def get_archive_list(self) -> List[Dict[str, Any]]:
        """アーカイブファイルのリストを取得
        
        Returns:
            アーカイブファイル情報のリスト
        """
        archives = []
        
        try:
            for archive_file in self.archive_dir.glob("generation_history_*.json.gz"):
                stat = archive_file.stat()
                archives.append({
                    "filename": archive_file.name,
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # 作成日時でソート（新しい順）
            archives.sort(key=lambda x: x["created"], reverse=True)
            
        except (IOError, OSError) as e:
            logger.error(f"I/O error listing archives: {type(e).__name__} - {e}")
            
        return archives
    
    def cleanup_old_archives(self, keep_count: int = 5) -> Dict[str, Any]:
        """古いアーカイブファイルを削除
        
        Args:
            keep_count: 保持するアーカイブファイル数
            
        Returns:
            削除結果の統計情報
        """
        archives = self.get_archive_list()
        
        if len(archives) <= keep_count:
            return {
                "status": "nothing_to_delete",
                "total_archives": len(archives),
                "keep_count": keep_count
            }
        
        # 削除対象を特定
        to_delete = archives[keep_count:]
        deleted = []
        
        for archive_info in to_delete:
            try:
                archive_path = self.archive_dir / archive_info["filename"]
                archive_path.unlink()
                deleted.append(archive_info["filename"])
                logger.info(f"Deleted old archive: {archive_info['filename']}")
            except (IOError, OSError) as e:
                logger.error(f"Failed to delete {archive_info['filename']}: {e}")
        
        return {
            "status": "completed",
            "deleted_count": len(deleted),
            "deleted_files": deleted,
            "remaining_count": keep_count
        }
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """データファイルの統計情報を取得
        
        Returns:
            各種データファイルの統計情報
        """
        stats = {
            "forecast_cache": {},
            "generation_history": {},
            "archives": {}
        }
        
        # forecast_cacheの統計
        total_rows = 0
        total_size_mb = 0
        file_count = 0
        
        try:
            for csv_file in self.forecast_cache_dir.glob("*.csv"):
                file_count += 1
                size_mb = csv_file.stat().st_size / (1024 * 1024)
                total_size_mb += size_mb
                
                # 行数をカウント
                with open(csv_file, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for _ in f) - 1  # ヘッダー行を除く
                    total_rows += row_count
            
            stats["forecast_cache"] = {
                "file_count": file_count,
                "total_rows": total_rows,
                "total_size_mb": round(total_size_mb, 2),
                "average_rows_per_file": round(total_rows / file_count, 2) if file_count > 0 else 0
            }
        except (IOError, OSError) as e:
            logger.error(f"I/O error getting forecast cache statistics: {e}")
            stats["forecast_cache"]["error"] = str(e)
        
        # generation_historyの統計
        try:
            if self.generation_history_file.exists():
                size_mb = self.generation_history_file.stat().st_size / (1024 * 1024)
                
                with open(self.generation_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entry_count = len(data)
                
                stats["generation_history"] = {
                    "exists": True,
                    "size_mb": round(size_mb, 2),
                    "entry_count": entry_count,
                    "needs_archive": size_mb >= self.history_max_size_mb
                }
            else:
                stats["generation_history"] = {"exists": False}
        except (IOError, OSError) as e:
            logger.error(f"I/O error getting generation history statistics: {e}")
            stats["generation_history"]["error"] = str(e)
        except json.JSONDecodeError as e:
            logger.error(f"JSON error getting generation history statistics: {e}")
            stats["generation_history"]["error"] = str(e)
        
        # アーカイブの統計
        archives = self.get_archive_list()
        total_archive_size = sum(a["size_mb"] for a in archives)
        
        stats["archives"] = {
            "count": len(archives),
            "total_size_mb": round(total_archive_size, 2),
            "latest": archives[0]["filename"] if archives else None
        }
        
        return stats


# コマンドラインインターフェース（デバッグ用）
if __name__ == "__main__":
    manager = DataManager()
    
    # 統計情報を表示
    print("=== Data Statistics ===")
    stats = manager.get_data_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # クリーンアップのデモ（実際には実行しない）
    print("\n=== Cleanup Demo (dry run) ===")
    print(f"Would clean forecast cache older than {manager.forecast_retention_days} days")
    print(f"Would archive generation history if size > {manager.history_max_size_mb}MB")