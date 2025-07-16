"""インデックス化されたCSVハンドラー - 高速なCSVデータアクセスを提供

このモジュールは、CSVファイルをインデックス化してメモリに保持し、
高速な検索を可能にします。ファイルハッシュによる変更検知と
自動再構築機能を提供します。
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime
import csv

from src.data.past_comment import PastComment, CommentType

logger = logging.getLogger(__name__)


class IndexedCSVHandler:
    """インデックス化されたCSVハンドラー"""
    
    def __init__(self, cache_dir: Path | None = None):
        """
        Args:
            cache_dir: インデックスキャッシュを保存するディレクトリ
        """
        self.cache_dir = cache_dir or Path("./cache/csv_indices")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # メモリキャッシュ
        self.index_cache: dict[str, dict[str, Any]] = {}
        self.file_hashes: dict[str, str] = {}
        
    def get_file_hash(self, file_path: Path) -> str:
        """ファイルのハッシュ値を計算"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def need_rebuild_index(self, csv_path: Path) -> bool:
        """インデックスの再構築が必要かチェック"""
        if not csv_path.exists():
            return False
            
        current_hash = self.get_file_hash(csv_path)
        cached_hash = self.file_hashes.get(str(csv_path))
        
        if cached_hash != current_hash:
            logger.info(f"File changed, need to rebuild index: {csv_path}")
            return True
            
        # メモリキャッシュにない場合
        if str(csv_path) not in self.index_cache:
            # ディスクキャッシュを確認
            index_path = self._get_index_path(csv_path)
            if not index_path.exists():
                return True
                
        return False
    
    def _get_index_path(self, csv_path: Path) -> Path:
        """インデックスファイルのパスを取得"""
        file_hash = self.get_file_hash(csv_path)
        index_name = f"{csv_path.stem}_{file_hash}.json"
        return self.cache_dir / index_name
    
    def load_indexed_csv(self, csv_path: Path, 
                        comment_type: CommentType,
                        season: str) -> list[PastComment]:
        """インデックス化されたCSVをロード"""
        if self.need_rebuild_index(csv_path):
            self._build_index(csv_path, comment_type, season)
            
        # メモリキャッシュから取得
        index = self.index_cache.get(str(csv_path))
        if index:
            return index.get("all_comments", [])
            
        # ディスクキャッシュから取得
        index = self._load_index_from_disk(csv_path)
        if index:
            self.index_cache[str(csv_path)] = index
            return index.get("all_comments", [])
            
        return []
    
    def search_by_weather(self, csv_path: Path, weather_condition: str) -> list[PastComment]:
        """天気条件で検索"""
        index = self._get_or_load_index(csv_path)
        if not index:
            return []
            
        weather_index = index.get("by_weather", {})
        results = []
        
        # 部分一致検索
        for key, comments in weather_index.items():
            if weather_condition in key or key in weather_condition:
                results.extend(comments)
                
        return results
    
    def search_by_usage_count(self, csv_path: Path, 
                             min_count: int = 0, 
                             max_count: int = float('inf')) -> list[PastComment]:
        """使用回数で検索"""
        index = self._get_or_load_index(csv_path)
        if not index:
            return []
            
        count_index = index.get("by_count", {})
        results = []
        
        for count_str, comments in count_index.items():
            count = int(count_str)
            if min_count <= count <= max_count:
                results.extend(comments)
                
        return results
    
    def _get_or_load_index(self, csv_path: Path) -> dict[str, Any | None]:
        """インデックスを取得（メモリまたはディスクから）"""
        # メモリキャッシュを確認
        if str(csv_path) in self.index_cache:
            return self.index_cache[str(csv_path)]
            
        # ディスクから読み込み
        index = self._load_index_from_disk(csv_path)
        if index:
            self.index_cache[str(csv_path)] = index
            
        return index
    
    def _build_index(self, csv_path: Path, comment_type: CommentType, season: str) -> None:
        """CSVファイルからインデックスを構築"""
        logger.info(f"Building index for: {csv_path}")
        
        index = {
            "by_weather": {},
            "by_count": {},
            "by_season": {},
            "all_comments": []
        }
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # PastCommentオブジェクトを作成
                    comment = self._create_past_comment(row, comment_type, season)
                    if not comment:
                        continue
                        
                    index["all_comments"].append(comment)
                    
                    # 天気条件でインデックス
                    weather = comment.weather_condition
                    if weather not in index["by_weather"]:
                        index["by_weather"][weather] = []
                    index["by_weather"][weather].append(comment)
                    
                    # 使用回数でインデックス
                    count_str = str(comment.usage_count)
                    if count_str not in index["by_count"]:
                        index["by_count"][count_str] = []
                    index["by_count"][count_str].append(comment)
                    
                    # 季節でインデックス
                    if season not in index["by_season"]:
                        index["by_season"][season] = []
                    index["by_season"][season].append(comment)
            
            # メモリキャッシュに保存
            self.index_cache[str(csv_path)] = index
            self.file_hashes[str(csv_path)] = self.get_file_hash(csv_path)
            
            # ディスクに保存
            self._save_index_to_disk(csv_path, index)
            
            logger.info(f"Index built: {len(index['all_comments'])} comments indexed")
            
        except Exception as e:
            logger.error(f"Failed to build index for {csv_path}: {e}")
    
    def _create_past_comment(self, row: dict[str, str], 
                           comment_type: CommentType, 
                           season: str) -> PastComment | None:
        """CSVの行からPastCommentオブジェクトを作成"""
        try:
            # カラム名の確認
            if comment_type == CommentType.WEATHER_COMMENT:
                comment_text = row.get('weather_comment', '').strip()
            else:
                comment_text = row.get('advice', '').strip()
                
            if not comment_text:
                return None
                
            return PastComment(
                comment_id=f"{season}_{comment_type.value}_{hash(comment_text)}",
                comment_text=comment_text,
                comment_type=comment_type,
                created_at=datetime.now(),
                location="",  # CSVには地点情報がない
                weather_condition=row.get('weather_condition', ''),
                temperature=float(row.get('temperature', 0)),
                season=season,
                usage_count=int(row.get('usage_count', 0)),
                # 天気コメントとアドバイスの組み合わせ
                comment1=row.get('weather_comment', ''),
                comment2=row.get('advice', '')
            )
        except Exception as e:
            logger.error(f"Failed to create PastComment: {e}")
            return None
    
    def _save_index_to_disk(self, csv_path: Path, index: dict[str, Any]) -> None:
        """インデックスをディスクに保存（アトミックな書き込みとリトライ機構付き）"""
        index_path = self._get_index_path(csv_path)
        temp_path = index_path.with_suffix('.tmp')
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                # PastCommentオブジェクトを辞書に変換
                serializable_index = self._convert_index_to_serializable(index)
                
                # 一時ファイルに書き込み
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_index, f, ensure_ascii=False, indent=2)
                
                # アトミックな移動（rename）
                temp_path.replace(index_path)
                logger.info(f"Index saved to: {index_path}")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to save index (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(retry_delay * (attempt + 1))  # エクスポネンシャルバックオフ
                else:
                    logger.error(f"Failed to save index after {max_retries} attempts: {e}")
                    # 一時ファイルのクリーンアップ
                    if temp_path.exists():
                        try:
                            temp_path.unlink()
                        except (OSError, PermissionError):
                            pass
    
    def _load_index_from_disk(self, csv_path: Path) -> dict[str, Any | None]:
        """ディスクからインデックスをロード"""
        index_path = self._get_index_path(csv_path)
        if not index_path.exists():
            return None
            
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                serializable_index = json.load(f)
            
            # 辞書をPastCommentオブジェクトに変換
            index = self._convert_index_from_serializable(serializable_index)
            
            logger.info(f"Index loaded from: {index_path}")
            return index
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return None
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self.index_cache.clear()
        self.file_hashes.clear()
        
        # ディスクキャッシュも削除（.idxと.jsonの両方を削除）
        for pattern in ["*.idx", "*.json"]:
            for index_file in self.cache_dir.glob(pattern):
                try:
                    index_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete index file {index_file}: {e}")
    
    def _convert_index_to_serializable(self, index: dict[str, Any]) -> dict[str, Any]:
        """インデックスをJSON用にシリアライズ可能な形式に変換"""
        serializable_index = {}
        
        for key, value in index.items():
            if key == "all_comments":
                serializable_index[key] = [self._comment_to_dict(c) for c in value]
            elif key in ["by_weather", "by_count", "by_season"]:
                serializable_index[key] = {}
                for sub_key, comments in value.items():
                    serializable_index[key][sub_key] = [self._comment_to_dict(c) for c in comments]
            else:
                serializable_index[key] = value
                
        return serializable_index
    
    def _convert_index_from_serializable(self, serializable_index: dict[str, Any]) -> dict[str, Any]:
        """JSON形式のインデックスをPastCommentオブジェクトに変換"""
        index = {}
        
        for key, value in serializable_index.items():
            if key == "all_comments":
                index[key] = [self._dict_to_comment(d) for d in value]
            elif key in ["by_weather", "by_count", "by_season"]:
                index[key] = {}
                for sub_key, dicts in value.items():
                    index[key][sub_key] = [self._dict_to_comment(d) for d in dicts]
            else:
                index[key] = value
                
        return index
    
    def _comment_to_dict(self, comment: PastComment) -> dict[str, Any]:
        """PastCommentオブジェクトを辞書に変換"""
        return {
            "comment_id": comment.comment_id,
            "comment_text": comment.comment_text,
            "comment_type": comment.comment_type.value,
            "created_at": comment.created_at.isoformat(),
            "location": comment.location,
            "weather_condition": comment.weather_condition,
            "temperature": comment.temperature,
            "season": comment.season,
            "usage_count": comment.usage_count,
            "comment1": comment.comment1,
            "comment2": comment.comment2
        }
    
    def _dict_to_comment(self, data: dict[str, Any]) -> PastComment:
        """辞書をPastCommentオブジェクトに変換"""
        return PastComment(
            comment_id=data["comment_id"],
            comment_text=data["comment_text"],
            comment_type=CommentType(data["comment_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            location=data["location"],
            weather_condition=data["weather_condition"],
            temperature=data["temperature"],
            season=data["season"],
            usage_count=data["usage_count"],
            comment1=data.get("comment1", ""),
            comment2=data.get("comment2", "")
        )