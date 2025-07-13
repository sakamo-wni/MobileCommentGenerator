"""HistoryManagerのテスト"""

import pytest
from unittest.mock import patch, Mock, MagicMock

from src.controllers.history_manager import HistoryManager


class TestHistoryManager:
    """HistoryManagerのテストクラス"""
    
    @pytest.fixture
    def manager(self):
        """テスト用のHistoryManagerインスタンス"""
        return HistoryManager()
    
    @pytest.fixture
    def sample_history(self):
        """テスト用の履歴データ"""
        return [
            {
                'timestamp': '2024-01-01 10:00:00',
                'location': '東京',
                'provider': 'gemini',
                'comment': '晴れの良い天気です'
            },
            {
                'timestamp': '2024-01-01 11:00:00',
                'location': '大阪',
                'provider': 'openai',
                'comment': '雨が降りそうです'
            },
            {
                'timestamp': '2024-01-01 12:00:00',
                'location': '東京',
                'provider': 'gemini',
                'comment': '曇りがちな天気です'
            }
        ]
    
    def test_generation_history_lazy_loading(self, manager, sample_history):
        """生成履歴の遅延読み込みテスト"""
        with patch('src.ui.streamlit_utils.load_history', return_value=sample_history):
            # 初回アクセス時に読み込まれる
            assert manager._generation_history is None
            history = manager.generation_history
            assert history == sample_history
            assert manager._generation_history == sample_history
            
            # 2回目はキャッシュから返される
            with patch('src.ui.streamlit_utils.load_history') as mock_load:
                history2 = manager.generation_history
                assert history2 == sample_history
                mock_load.assert_not_called()
    
    def test_save_generation_result_success(self, manager):
        """成功した結果の保存テスト"""
        result = {
            'success': True,
            'final_comment': 'テストコメント',
            'generation_metadata': {'temperature': 25}
        }
        
        with patch('src.ui.streamlit_utils.save_to_history') as mock_save:
            manager.save_generation_result(result, '東京', 'gemini')
            
            # save_to_historyが呼ばれる
            mock_save.assert_called_once_with(result, '東京', 'gemini')
            
            # キャッシュがクリアされる
            assert manager._generation_history is None
    
    def test_save_generation_result_failure(self, manager):
        """失敗した結果は保存されないテスト"""
        result = {
            'success': False,
            'error': 'エラーが発生しました'
        }
        
        with patch('src.ui.streamlit_utils.save_to_history') as mock_save:
            manager.save_generation_result(result, '東京', 'gemini')
            
            # save_to_historyが呼ばれない
            mock_save.assert_not_called()
            
            # キャッシュはそのまま
            assert manager._generation_history is None
    
    def test_clear_cache(self, manager, sample_history):
        """キャッシュクリアのテスト"""
        # まず履歴を読み込む
        with patch('src.ui.streamlit_utils.load_history', return_value=sample_history):
            _ = manager.generation_history
            assert manager._generation_history is not None
        
        # キャッシュをクリア
        manager.clear_cache()
        assert manager._generation_history is None
    
    def test_get_recent_history(self, manager, sample_history):
        """最近の履歴取得テスト"""
        with patch('src.ui.streamlit_utils.load_history', return_value=sample_history):
            # デフォルトは10件まで
            recent = manager.get_recent_history()
            assert len(recent) == 3  # サンプルは3件なので全部返される
            
            # 制限を指定
            recent = manager.get_recent_history(limit=2)
            assert len(recent) == 2
            # 最新の2件が返される
            assert recent[0]['timestamp'] == '2024-01-01 11:00:00'
            assert recent[1]['timestamp'] == '2024-01-01 12:00:00'
    
    def test_get_recent_history_empty(self, manager):
        """履歴が空の場合のテスト"""
        with patch('src.ui.streamlit_utils.load_history', return_value=[]):
            recent = manager.get_recent_history()
            assert recent == []
    
    def test_get_history_by_location(self, manager, sample_history):
        """地点別履歴取得テスト"""
        with patch('src.ui.streamlit_utils.load_history', return_value=sample_history):
            # 東京の履歴のみ取得
            tokyo_history = manager.get_history_by_location('東京')
            assert len(tokyo_history) == 2
            assert all(h['location'] == '東京' for h in tokyo_history)
            
            # 大阪の履歴のみ取得
            osaka_history = manager.get_history_by_location('大阪')
            assert len(osaka_history) == 1
            assert osaka_history[0]['location'] == '大阪'
            
            # 存在しない地点
            kyoto_history = manager.get_history_by_location('京都')
            assert kyoto_history == []
    
    @patch('src.ui.streamlit_utils.load_history')
    @patch('src.ui.streamlit_utils.save_to_history')
    @patch('src.controllers.history_manager.logger')
    def test_logging(self, mock_logger, mock_save, mock_load, manager):
        """ログ出力のテスト"""
        mock_load.return_value = []
        
        # 成功結果の保存時にログが出力される
        result = {'success': True, 'final_comment': 'test'}
        manager.save_generation_result(result, '東京', 'gemini')
        
        mock_logger.info.assert_called_with(
            "Saved to history: location=東京, provider=gemini"
        )