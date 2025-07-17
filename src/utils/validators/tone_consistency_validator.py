"""トーンと態度の一貫性を検証するバリデータ"""

from __future__ import annotations
import logging
import yaml
from pathlib import Path
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class ToneConsistencyValidator:
    """コメントペアのトーンと態度の一貫性を検証"""
    
    def __init__(self):
        """設定ファイルから単語リストを読み込み"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "validator_words.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.tone_words = config.get('tone_words', {})
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}. デフォルト値を使用します。")
            self.tone_words = self._get_default_tone_words()
    
    def _get_default_tone_words(self) -> dict:
        """デフォルトのトーン単語設定を返す"""
        return {
            'positive': ["素晴らしい", "気持ちいい", "最高", "快適", "爽やか",
                        "楽しい", "嬉しい", "ワクワク", "期待", "チャンス"],
            'negative': ["最悪", "ひどい", "危険", "警戒", "注意",
                        "厳しい", "辛い", "困難", "大変", "心配"],
            'urgency': ["警報", "緊急", "即座に", "至急", "危険",
                       "警戒", "厳重", "必ず", "絶対に"],
            'casual': ["のんびり", "ゆっくり", "まったり", "気楽に",
                      "適当に", "ぼちぼち", "ほどほどに"],
            'encouraging': ["頑張", "乗り切", "大丈夫", "きっと", "応援",
                           "ファイト", "元気", "前向き"]
        }
    
    def check_tone_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        天気コメントとアドバイスのトーンが矛盾していないかチェック
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            weather_data: 天気データ（参考情報）
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # ポジティブ・ネガティブトーンの判定
        positive_weather = self._has_positive_tone(weather_comment)
        positive_advice = self._has_positive_tone(advice_comment)
        negative_weather = self._has_negative_tone(weather_comment)
        negative_advice = self._has_negative_tone(advice_comment)
        
        # 極端なトーンの不一致をチェック
        if positive_weather and negative_advice:
            return False, "天気コメントが前向きなのにアドバイスが否定的"
        
        if negative_weather and positive_advice:
            # ただし、悪天候でも前向きなアドバイスは許容する場合がある
            if not self._is_encouraging_advice(advice_comment):
                return False, "天気コメントが否定的なのにアドバイスが楽観的すぎる"
        
        # 緊急性のレベル不一致
        urgent_weather = self._has_urgent_tone(weather_comment)
        casual_advice = self._has_casual_tone(advice_comment)
        
        if urgent_weather and casual_advice:
            return False, "天気が緊急性を示しているのにアドバイスが軽すぎる"
        
        return True, ""
    
    def _has_positive_tone(self, text: str) -> bool:
        """ポジティブなトーンかチェック"""
        positive_words = self.tone_words.get('positive', [])
        return any(word in text for word in positive_words)
    
    def _has_negative_tone(self, text: str) -> bool:
        """ネガティブなトーンかチェック"""
        negative_words = self.tone_words.get('negative', [])
        return any(word in text for word in negative_words)
    
    def _has_urgent_tone(self, text: str) -> bool:
        """緊急性のあるトーンかチェック"""
        urgent_words = self.tone_words.get('urgency', [])
        return any(word in text for word in urgent_words)
    
    def _has_casual_tone(self, text: str) -> bool:
        """カジュアルなトーンかチェック"""
        casual_words = self.tone_words.get('casual', [])
        return any(word in text for word in casual_words)
    
    def _is_encouraging_advice(self, text: str) -> bool:
        """励ましのアドバイスかチェック"""
        encouraging_words = self.tone_words.get('encouraging', [])
        return any(word in text for word in encouraging_words)