"""天気コメント生成システム - コントローラー（ビジネスロジック）"""

import logging
from datetime import datetime
from typing import Any

import pytz

from app_interfaces import ICommentGenerationController
from src.config.app_config import AppConfig, get_config
from src.types import BatchGenerationResult, LocationResult
from src.ui.streamlit_utils import load_history, load_locations, save_to_history
from src.utils.error_handler import ErrorHandler
from src.workflows.comment_generation_workflow import run_comment_generation

logger = logging.getLogger(__name__)


class CommentGenerationController(ICommentGenerationController):
    """コメント生成のビジネスロジックを管理するコントローラー"""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_config()
        self._generation_history = None

    @property
    def generation_history(self) -> list[dict[str, Any]]:
        """生成履歴を取得（遅延読み込み）"""
        if self._generation_history is None:
            self._generation_history = load_history()
        return self._generation_history

    def get_default_locations(self) -> list[str]:
        """デフォルトの地点リストを取得"""
        return load_locations()

    def get_default_llm_provider(self) -> str:
        """デフォルトのLLMプロバイダーを取得"""
        return self.config.ui_settings.default_llm_provider

    def validate_configuration(self) -> dict[str, Any]:
        """設定の検証"""
        return self.config.validate()

    def get_config_dict(self) -> dict[str, Any]:
        """設定を辞書形式で取得"""
        return self.config.to_dict()

    def generate_comment_for_location(self, location: str, llm_provider: str) -> LocationResult:
        """単一地点のコメント生成"""
        try:
            # 実際のコメント生成
            result = run_comment_generation(
                location_name=location,
                target_datetime=datetime.now(),
                llm_provider=llm_provider
            )

            # 結果を収集
            location_result = {
                'location': location,
                'result': result,
                'success': result.get('success', False),
                'comment': result.get('final_comment', ''),
                'error': result.get('error', None)
            }

            # ソースファイル情報を抽出
            metadata = result.get('generation_metadata', {})
            if metadata.get('selected_past_comments'):
                sources = []
                for comment in metadata['selected_past_comments']:
                    if 'source_file' in comment:
                        sources.append(comment['source_file'])
                if sources:
                    location_result['source_files'] = sources
                    # 詳細ログ出力
                    logger.info(f"地点: {location}")
                    logger.info(f"  天気: {metadata.get('weather_condition', '不明')}")
                    logger.info(f"  気温: {metadata.get('temperature', '不明')}°C")
                    logger.info(f"  コメント生成元ファイル: {sources}")
                    logger.info(f"  生成コメント: {result.get('final_comment', '')}")

            # 履歴に保存
            if result.get('success'):
                save_to_history(result, location, llm_provider)
                # 履歴キャッシュをクリア
                self._generation_history = None

            return location_result

        except Exception as e:
            # エラーハンドリング
            return ErrorHandler.create_error_result(location, e)

    def generate_comments_batch(self, locations: list[str], llm_provider: str,
                                progress_callback=None) -> BatchGenerationResult:
        """複数地点のコメント生成

        Args:
            locations: 生成対象の地点リスト
            llm_provider: 使用するLLMプロバイダー
            progress_callback: 進捗通知用コールバック関数
                              シグネチャ: (idx: int, total: int, location: str) -> None
                              - idx: 現在の処理インデックス（0ベース）
                              - total: 全体の地点数
                              - location: 現在処理中の地点名

        Returns:
            BatchGenerationResult: バッチ生成結果
        """
        if not locations:
            return {'success': False, 'error': '地点が選択されていません'}

        all_results = []
        total_locations = len(locations)

        try:
            for idx, location in enumerate(locations):
                # 進捗コールバック
                if progress_callback:
                    progress_callback(idx, total_locations, location)

                # 個別地点の生成
                location_result = self.generate_comment_for_location(location, llm_provider)
                all_results.append(location_result)

            # 成功数をカウント
            success_count = sum(1 for r in all_results if r['success'])

            # エラーがあった場合は詳細を収集
            errors = [r for r in all_results if not r['success']]
            error_messages = []

            for err in errors:
                location = err['location']
                error_msg = err.get('error', '不明なエラー')
                error_messages.append(f"{location}: {error_msg}")

            return {
                'success': success_count > 0,
                'total_locations': total_locations,
                'success_count': success_count,
                'results': all_results,
                'final_comment': '\n'.join([f"{r['location']}: {r['comment']}" for r in all_results if r['success']]),
                'errors': error_messages
            }

        except Exception as e:
            # 統一されたエラーハンドリング
            error_response = ErrorHandler.handle_error(e)
            return {
                'success': False,
                'error': error_response.error_message,
                'final_comment': None,
                'hint': error_response.hint
            }

    def format_forecast_time(self, forecast_time: str) -> str:
        """予報時刻をフォーマット"""
        try:
            # UTC時刻をパース
            dt = datetime.fromisoformat(forecast_time.replace('Z', '+00:00'))
            # JSTに変換
            jst = pytz.timezone('Asia/Tokyo')
            dt_jst = dt.astimezone(jst)
            return dt_jst.strftime('%Y年%m月%d日 %H時')
        except Exception as e:
            logger.warning(f"予報時刻のパース失敗: {e}, forecast_time={forecast_time}")
            return forecast_time

    def extract_weather_metadata(self, result: LocationResult) -> dict[str, Any]:
        """結果から天気メタデータを抽出"""
        metadata = {}

        if result.get('result') and result['result'].get('generation_metadata'):
            gen_metadata = result['result']['generation_metadata']

            # 基本情報
            metadata['forecast_time'] = gen_metadata.get('weather_forecast_time')
            metadata['temperature'] = gen_metadata.get('temperature')
            metadata['weather_condition'] = gen_metadata.get('weather_condition')
            metadata['wind_speed'] = gen_metadata.get('wind_speed')
            metadata['humidity'] = gen_metadata.get('humidity')

            # 選択されたコメント情報
            selection_meta = gen_metadata.get('selection_metadata', {})
            if selection_meta:
                metadata['selected_weather_comment'] = selection_meta.get('selected_weather_comment')
                metadata['selected_advice_comment'] = selection_meta.get('selected_advice_comment')
                metadata['llm_provider'] = selection_meta.get('llm_provider')

        return metadata

    def validate_location_count(self, locations: list[str]) -> tuple[bool, str | None]:
        """地点数の検証"""
        max_locations = self.config.ui_settings.max_locations_per_generation

        if len(locations) > max_locations:
            return False, f"選択された地点数が上限（{max_locations}地点）を超えています。"

        return True, None
