"""
Template loader for prompt builder

プロンプトテンプレートの読み込みを管理
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional

from .models import PromptTemplate

logger = logging.getLogger(__name__)


class TemplateLoader:
    """テンプレートファイルの読み込みを管理"""

    def __init__(self, template_dir: Optional[Path] = None, strict_validation: bool = False):
        """
        Args:
            template_dir: テンプレートディレクトリのパス
            strict_validation: 厳格な検証モード。Trueの場合、検証エラーで例外を発生
        """
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        self.strict_validation = strict_validation

    def load_text_file(self, filename: str) -> str:
        """テキストファイルを読み込み
        
        Args:
            filename: ファイル名
            
        Returns:
            ファイルの内容
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            Exception: その他の読み込みエラー
        """
        file_path = self.template_dir / filename
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"テンプレートファイルが見つかりません: {filename} ({file_path})")
            raise
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {filename} - {e}")
            raise

    def load_json_file(self, filename: str) -> dict[str, str]:
        """JSONファイルを読み込み
        
        Args:
            filename: ファイル名
            
        Returns:
            JSONデータ（辞書）
        """
        file_path = self.template_dir / filename
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"JSONファイルが見つかりません: {filename} ({file_path})")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {filename} - {e}")
            return {}
        except Exception as e:
            logger.error(f"JSON読み込みエラー: {filename} - {e}")
            return {}

    def load_all_templates(self) -> PromptTemplate:
        """すべてのテンプレートを読み込み
        
        Returns:
            PromptTemplate インスタンス
            
        Raises:
            ValueError: strict_validationモードで検証エラーが発生した場合
        """
        try:
            template = PromptTemplate(
                base_template=self.load_text_file("base.txt"),
                weather_specific=self.load_json_file("weather_specific.json"),
                seasonal_adjustments=self.load_json_file("seasonal_adjustments.json"),
                time_specific=self.load_json_file("time_specific.json"),
                fallback_template=self.load_text_file("fallback.txt"),
                example_templates=self.load_json_file("examples.json")
            )
            
            # テンプレートバリデーション
            self._validate_templates(template)
            
            return template
        except ValueError:
            # 検証エラーは再発生させる（strict_validationモードのため）
            raise
        except Exception as e:
            logger.error(f"テンプレート読み込み失敗、デフォルトを使用: {e}")
            return self._get_default_templates()

    def _validate_templates(self, template: PromptTemplate) -> None:
        """テンプレートの妥当性を検証
        
        Args:
            template: 検証対象のテンプレート
            
        Raises:
            ValueError: 検証エラーの場合（strict_validationモード時）
        """
        errors = []
        
        # 基本テンプレートの検証
        if not template.base_template:
            errors.append("基本テンプレートが空です")
        
        # 必須プレースホルダーの確認
        required_placeholders = ["{weather_info}", "{weather_comments}", "{advice_comments}"]
        for placeholder in required_placeholders:
            if placeholder not in template.base_template:
                errors.append(f"基本テンプレートに必須プレースホルダー {placeholder} がありません")
        
        # 天気別テンプレートの検証
        if not template.weather_specific:
            errors.append("天気別テンプレートが空です")
        else:
            required_weather_types = ["晴れ", "雨", "曇り", "雪"]
            for weather_type in required_weather_types:
                if weather_type not in template.weather_specific:
                    errors.append(f"天気別テンプレートに '{weather_type}' の定義がありません")
        
        # エラーがある場合の処理
        if errors:
            error_msg = "テンプレート検証エラー:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            
            if self.strict_validation:
                raise ValueError(error_msg)

    def _get_default_templates(self) -> PromptTemplate:
        """デフォルトテンプレートを生成
        
        Returns:
            デフォルトのPromptTemplate
        """
        return PromptTemplate(
            base_template=self._get_default_base_template(),
            weather_specific=self._get_default_weather_specific(),
            seasonal_adjustments={},
            time_specific={},
            fallback_template=self._get_default_fallback_template(),
            example_templates={}
        )

    def _get_default_base_template(self) -> str:
        """デフォルトの基本テンプレート"""
        return """現在の天気情報と過去の天気コメントのペアを参考に、最適な天気コメントを生成してください。

## 天気情報
{weather_info}

## 天気コメント候補（過去のデータから）
{weather_comments}

## 対応アドバイス候補（過去のデータから）
{advice_comments}

## 生成ルール
1. 必ず天気コメントとアドバイスの2つを生成してください
2. 天気コメントは現在の天気状況を簡潔に表現してください
3. アドバイスは具体的で実用的な内容にしてください
4. 各コメントは20文字以内にしてください
5. 絵文字は使用しないでください

## 期待する出力形式
天気コメント: [ここに天気コメント]
アドバイス: [ここにアドバイス]"""

    def _get_default_weather_specific(self) -> dict[str, str]:
        """デフォルトの天気別テンプレート"""
        return {
            "晴れ": "晴天の特徴を活かしたコメントを生成してください。",
            "雨": "雨天に適したコメントを生成してください。傘の必要性に言及してください。",
            "曇り": "曇り空の特徴を活かしたコメントを生成してください。",
            "雪": "雪に関する注意事項を含めたコメントを生成してください。"
        }

    def _get_default_fallback_template(self) -> str:
        """デフォルトのフォールバックテンプレート"""
        return """シンプルな天気コメントを生成してください。

天気: {weather}
気温: {temperature}°C

20文字以内で簡潔にまとめてください。"""