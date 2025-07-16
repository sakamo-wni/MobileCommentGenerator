#!/usr/bin/env python3
"""
設定検証CLIコマンド

使用方法:
    python -m src.config.validate
"""

from __future__ import annotations
import sys
import json
import logging

logger = logging.getLogger(__name__)
from typing import Any

from .app_settings import get_config, validate_config, setup_environment_defaults


def format_errors(errors: dict[str, list[str]]) -> str:
    """エラーを整形して表示用文字列を生成
    
    Args:
        errors: カテゴリ別のエラーメッセージ
        
    Returns:
        整形されたエラーメッセージ
    """
    lines = []
    for category, error_list in errors.items():
        lines.append(f"\n[{category}]")
        for error in error_list:
            lines.append(f"  ✗ {error}")
    return "\n".join(lines)


def print_config_summary(config_dict: dict[str, Any]) -> None:
    """設定のサマリーを表示
    
    Args:
        config_dict: 設定の辞書表現
    """
    logger.info("\n=== 設定サマリー ===")
    
    # Weather設定
    weather = config_dict.get("weather", {})
    logger.info(f"\n[Weather設定]")
    logger.info(f"  - APIキー: {'設定済み' if weather.get('wxtech_api_key', '***') != '***' else '未設定'}")
    logger.info(f"  - デフォルト地点: {weather.get('default_location', 'N/A')}")
    logger.info(f"  - 予報時間: {weather.get('forecast_hours', 'N/A')}時間")
    logger.info(f"  - キャッシュ: {'有効' if weather.get('enable_caching', False) else '無効'}")
    
    # LangGraph設定
    langgraph = config_dict.get("langgraph", {})
    logger.info(f"\n[LangGraph設定]")
    logger.info(f"  - 天気統合: {'有効' if langgraph.get('enable_weather_integration', False) else '無効'}")
    logger.info(f"  - 自動地点検出: {'有効' if langgraph.get('auto_location_detection', False) else '無効'}")
    logger.info(f"  - 信頼度閾値: {langgraph.get('min_confidence_threshold', 'N/A')}")
    
    # アプリケーション設定
    logger.info(f"\n[アプリケーション設定]")
    logger.info(f"  - デバッグモード: {'有効' if config_dict.get('debug_mode', False) else '無効'}")
    logger.info(f"  - ログレベル: {config_dict.get('log_level', 'N/A')}")


def main() -> int:
    """メイン処理
    
    Returns:
        終了コード（0: 成功、1: エラー）
    """
    logger.info("設定の検証を開始します...")
    
    try:
        # デフォルト値を設定
        setup_environment_defaults()
        
        # 設定を読み込み
        config = get_config()
        
        # 設定を検証
        errors = validate_config(config)
        
        if errors:
            logger.info("\n❌ 設定にエラーが見つかりました:")
            logger.info(format_errors(errors))
            
            # 詳細情報の表示
            logger.info("\n\n=== 詳細情報 ===")
            logger.info("環境変数の設定を確認してください。")
            logger.info("必要な環境変数の一覧は src/config/env_migration_guide.md を参照してください。")
            
            return 1
        else:
            logger.info("\n✅ 設定の検証に成功しました!")
            
            # 設定のサマリーを表示
            config_dict = config.to_dict()
            print_config_summary(config_dict)
            
            # JSON形式での出力オプション
            if "--json" in sys.argv:
                logger.info("\n\n=== JSON形式の設定 ===")
                logger.info(json.dumps(config_dict, indent=2, ensure_ascii=False))
            
            return 0
            
    except Exception as e:
        logger.info(f"\n❌ 予期しないエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())