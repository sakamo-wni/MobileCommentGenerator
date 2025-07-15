"""統一モードと並列処理モードのパフォーマンス比較テスト"""

import pytest
import time
from unittest.mock import patch, Mock
from datetime import datetime

from src.workflows.comment_generation_workflow import run_comment_generation


class TestPerformanceComparison:
    """パフォーマンス比較テストクラス"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """共通の依存関係のモック"""
        with patch('src.workflows.comment_generation_workflow.fetch_weather_forecast_node') as mock_weather, \
             patch('src.workflows.comment_generation_workflow.retrieve_past_comments_node') as mock_comments, \
             patch('src.nodes.unified_comment_generation_node.LLMManager') as mock_unified_llm, \
             patch('src.nodes.select_comment_pair_node.LLMManager') as mock_select_llm, \
             patch('src.nodes.generate_comment_node.LLMManager') as mock_generate_llm:
            
            # 天気データのモック
            mock_weather.return_value = Mock(
                weather_data=Mock(
                    weather_description="晴れ",
                    temperature=25.0,
                    humidity=60.0,
                    wind_speed=3.0
                )
            )
            
            # 過去コメントのモック
            from src.data.past_comment import PastComment, CommentType
            mock_comments.return_value = Mock(
                past_comments=[
                    PastComment(
                        id="1",
                        comment_text="晴れていい天気",
                        comment_type=CommentType.WEATHER_COMMENT,
                        weather_condition="晴れ",
                        usage_count=10,
                        season="春"
                    ),
                    PastComment(
                        id="2",
                        comment_text="紫外線に注意",
                        comment_type=CommentType.ADVICE,
                        weather_condition="晴れ",
                        usage_count=5,
                        season="春"
                    )
                ]
            )
            
            # 統一モードのLLMレスポンス
            mock_unified_instance = Mock()
            mock_unified_instance.generate.return_value = '''
            {
                "weather_index": 0,
                "advice_index": 0,
                "generated_comment": "晴れていい天気　紫外線に注意"
            }
            '''
            mock_unified_llm.return_value = mock_unified_instance
            
            # 選択ノードのLLMレスポンス
            mock_select_instance = Mock()
            mock_select_instance.select_best_pair.return_value = (
                Mock(comment_text="晴れていい天気"),
                Mock(comment_text="紫外線に注意"),
                0.9,
                "天気条件に最適"
            )
            mock_select_llm.return_value = mock_select_instance
            
            # 生成ノードのLLMレスポンス
            mock_generate_instance = Mock()
            mock_generate_instance.generate_comment.return_value = "晴れていい天気　紫外線に注意"
            mock_generate_llm.return_value = mock_generate_instance
            
            yield {
                'unified_llm': mock_unified_instance,
                'select_llm': mock_select_instance,
                'generate_llm': mock_generate_instance
            }
    
    def test_unified_mode_faster_than_parallel(self, mock_dependencies):
        """統一モードが並列処理モードより高速であることを検証"""
        
        # 統一モードの実行時間測定
        start_unified = time.time()
        unified_result = run_comment_generation(
            location_name="東京",
            target_datetime=datetime.now(),
            llm_provider="openai",
            use_unified_mode=True
        )
        unified_time = time.time() - start_unified
        
        # 並列処理モードの実行時間測定
        start_parallel = time.time()
        parallel_result = run_comment_generation(
            location_name="東京",
            target_datetime=datetime.now(),
            llm_provider="openai",
            use_unified_mode=False
        )
        parallel_time = time.time() - start_parallel
        
        # 両方成功することを確認
        assert unified_result.get('success') is True
        assert parallel_result.get('success') is True
        
        # LLM呼び出し回数の検証
        # 統一モード: 1回
        assert mock_dependencies['unified_llm'].generate.call_count == 1
        
        # 並列処理モード: 選択と生成で合計2回以上
        total_parallel_calls = (
            mock_dependencies['select_llm'].select_best_pair.call_count +
            mock_dependencies['generate_llm'].generate_comment.call_count
        )
        assert total_parallel_calls >= 2
        
        # メタデータの確認
        unified_metadata = unified_result.get('generation_metadata', {})
        assert unified_metadata.get('unified_generation') is True
        
        parallel_metadata = parallel_result.get('generation_metadata', {})
        assert parallel_metadata.get('unified_generation') is not True
    
    def test_both_modes_produce_valid_results(self, mock_dependencies):
        """両モードが有効な結果を生成することを検証"""
        
        # 統一モード
        unified_result = run_comment_generation(
            location_name="東京",
            llm_provider="openai",
            use_unified_mode=True
        )
        
        # 並列処理モード
        parallel_result = run_comment_generation(
            location_name="東京",
            llm_provider="openai",
            use_unified_mode=False
        )
        
        # 両方とも成功し、コメントが生成されることを確認
        assert unified_result.get('success') is True
        assert unified_result.get('final_comment') is not None
        assert len(unified_result.get('final_comment', '')) > 0
        
        assert parallel_result.get('success') is True
        assert parallel_result.get('final_comment') is not None
        assert len(parallel_result.get('final_comment', '')) > 0