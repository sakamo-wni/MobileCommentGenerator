"""WorkflowExecutorのテスト"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

from src.workflows.workflow_executor import (
    WorkflowStateBuilder,
    WorkflowResultParser,
    WorkflowResponseBuilder,
    WorkflowExecutor
)
from src.exceptions.error_types import (
    WeatherFetchError, DataAccessError, LLMError, AppException, ErrorType
)


class TestWorkflowStateBuilder:
    """WorkflowStateBuilderのテストクラス"""
    
    @patch('src.workflows.workflow_executor.get_config')
    def test_build_initial_state_default(self, mock_get_config):
        """デフォルト値での初期状態構築テスト"""
        # 設定のモック
        mock_config = Mock()
        mock_config.weather.forecast_hours_ahead = 3
        mock_get_config.return_value = mock_config
        
        # 現在時刻をモック
        test_now = datetime(2024, 1, 1, 12, 0, 0)
        with patch('src.workflows.workflow_executor.datetime') as mock_datetime:
            mock_datetime.now.return_value = test_now
            
            state = WorkflowStateBuilder.build_initial_state(
                location_name="東京"
            )
        
        assert state['location_name'] == "東京"
        assert state['target_datetime'] == test_now + timedelta(hours=3)
        assert state['llm_provider'] == "openai"
        assert state['exclude_previous'] is False
        assert state['retry_count'] == 0
        assert state['errors'] == []
        assert state['warnings'] == []
        assert state['workflow_start_time'] == test_now
    
    def test_build_initial_state_with_params(self):
        """パラメータ指定での初期状態構築テスト"""
        target_dt = datetime(2024, 1, 2, 15, 0, 0)
        
        with patch('src.workflows.workflow_executor.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.weather.forecast_hours_ahead = 3
            mock_get_config.return_value = mock_config
            
            state = WorkflowStateBuilder.build_initial_state(
                location_name="大阪",
                target_datetime=target_dt,
                llm_provider="gemini",
                exclude_previous=True,
                custom_param="test_value"
            )
        
        assert state['location_name'] == "大阪"
        assert state['target_datetime'] == target_dt
        assert state['llm_provider'] == "gemini"
        assert state['exclude_previous'] is True
        assert state['custom_param'] == "test_value"
    
    def test_build_initial_state_with_pre_fetched_weather(self):
        """事前取得天気データありの初期状態構築テスト"""
        weather_data = {'temperature': 25, 'condition': 'sunny'}
        
        with patch('src.workflows.workflow_executor.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.weather.forecast_hours_ahead = 3
            mock_get_config.return_value = mock_config
            
            state = WorkflowStateBuilder.build_initial_state(
                location_name="京都",
                pre_fetched_weather=weather_data
            )
        
        assert state['pre_fetched_weather'] == weather_data


class TestWorkflowResultParser:
    """WorkflowResultParserのテストクラス"""
    
    def test_parse_output_json_success(self):
        """正常なJSON解析のテスト"""
        result = {
            'generation_metadata': {
                'output_json': json.dumps({
                    'final_comment': 'テストコメント',
                    'generation_metadata': {'score': 0.95}
                })
            }
        }
        
        comment, metadata = WorkflowResultParser.parse_output_json(result)
        assert comment == 'テストコメント'
        assert metadata == {'score': 0.95}
    
    def test_parse_output_json_invalid(self):
        """不正なJSON解析のテスト"""
        result = {
            'generation_metadata': {
                'output_json': '{"invalid json'
            }
        }
        
        with patch('src.workflows.workflow_executor.logger') as mock_logger:
            comment, metadata = WorkflowResultParser.parse_output_json(result)
            mock_logger.error.assert_called()
        
        # フォールバックで元のmetadataが返される
        assert comment is None
        assert metadata == {'output_json': '{"invalid json'}
    
    def test_parse_output_json_fallback(self):
        """フォールバック処理のテスト"""
        result = {
            'final_comment': 'フォールバックコメント',
            'generation_metadata': {'fallback': True}
        }
        
        comment, metadata = WorkflowResultParser.parse_output_json(result)
        assert comment == 'フォールバックコメント'
        assert metadata == {'fallback': True}
    
    def test_calculate_execution_time(self):
        """実行時間計算のテスト"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 5)  # 5秒後
        
        exec_time = WorkflowResultParser.calculate_execution_time(start_time, end_time)
        assert exec_time == 5000.0  # ミリ秒
    
    def test_calculate_execution_time_default_end(self):
        """終了時刻未指定の実行時間計算テスト"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch('src.workflows.workflow_executor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 2)
            exec_time = WorkflowResultParser.calculate_execution_time(start_time)
            assert exec_time == 2000.0


class TestWorkflowResponseBuilder:
    """WorkflowResponseBuilderのテストクラス"""
    
    def test_build_success_response(self):
        """成功レスポンス構築のテスト"""
        response = WorkflowResponseBuilder.build_success_response(
            final_comment="成功コメント",
            generation_metadata={'key': 'value'},
            execution_time_ms=1500.0,
            retry_count=2,
            warnings=['警告1']
        )
        
        assert response['success'] is True
        assert response['final_comment'] == "成功コメント"
        assert response['generation_metadata'] == {'key': 'value'}
        assert response['execution_time_ms'] == 1500.0
        assert response['retry_count'] == 2
        assert response['warnings'] == ['警告1']
    
    def test_build_error_response(self):
        """エラーレスポンス構築のテスト"""
        response = WorkflowResponseBuilder.build_error_response(
            errors=['エラー1', 'エラー2'],
            generation_metadata={'error': True},
            execution_time_ms=500.0,
            retry_count=0,
            warnings=[]
        )
        
        assert response['success'] is False
        assert response['error'] == "エラー1; エラー2"
        assert response['final_comment'] is None
        assert response['generation_metadata'] == {'error': True}
    
    def test_build_exception_response(self):
        """例外レスポンス構築のテスト"""
        exception = Exception("テスト例外")
        
        with patch.object(WorkflowResponseBuilder, '_classify_error') as mock_classify:
            mock_error = Mock()
            mock_classify.return_value = mock_error
            
            with patch('src.utils.error_handler.ErrorHandler.handle_error') as mock_handle:
                mock_response = Mock()
                mock_response.user_message = "ユーザー向けメッセージ"
                mock_response.error_type = "TEST_ERROR"
                mock_response.error_details = {'detail': 'test'}
                mock_handle.return_value = mock_response
                
                response = WorkflowResponseBuilder.build_exception_response(exception)
        
        assert response['success'] is False
        assert response['error'] == "ユーザー向けメッセージ"
        assert response['error_type'] == "TEST_ERROR"
        assert response['error_details'] == {'detail': 'test'}
    
    def test_classify_error(self):
        """エラー分類のテスト"""
        # 天気予報エラー
        error = WorkflowResponseBuilder._classify_error("天気予報の取得に失敗しました")
        assert isinstance(error, WeatherFetchError)
        
        # データアクセスエラー
        error = WorkflowResponseBuilder._classify_error("過去コメントが存在しません")
        assert isinstance(error, DataAccessError)
        
        # LLMエラー
        error = WorkflowResponseBuilder._classify_error("コメントの生成に失敗しました")
        assert isinstance(error, LLMError)
        
        # 不明なエラー
        error = WorkflowResponseBuilder._classify_error("不明なエラー")
        assert isinstance(error, AppException)
        assert error.error_type == ErrorType.UNKNOWN_ERROR


class TestWorkflowExecutor:
    """WorkflowExecutorのテストクラス"""
    
    @pytest.fixture
    def mock_workflow(self):
        """モックワークフロー"""
        workflow = Mock()
        return workflow
    
    @pytest.fixture
    def executor(self, mock_workflow):
        """テスト用のWorkflowExecutorインスタンス"""
        return WorkflowExecutor(mock_workflow)
    
    def test_execute_success(self, executor, mock_workflow):
        """正常実行のテスト"""
        # ワークフローの結果をモック
        workflow_result = {
            'workflow_start_time': datetime(2024, 1, 1, 12, 0, 0),
            'final_comment': '成功したコメント',
            'generation_metadata': {
                'output_json': json.dumps({
                    'final_comment': '成功したコメント',
                    'generation_metadata': {'success': True}
                })
            },
            'retry_count': 0,
            'warnings': [],
            'errors': []
        }
        mock_workflow.invoke.return_value = workflow_result
        
        result = executor.execute(
            location_name="東京",
            llm_provider="gemini"
        )
        
        assert result['success'] is True
        assert result['final_comment'] == '成功したコメント'
        assert 'execution_time_ms' in result
    
    def test_execute_with_errors(self, executor, mock_workflow):
        """エラーありの実行テスト"""
        workflow_result = {
            'workflow_start_time': datetime(2024, 1, 1, 12, 0, 0),
            'errors': ['エラー1', 'エラー2'],
            'generation_metadata': {},
            'retry_count': 3,
            'warnings': ['警告']
        }
        mock_workflow.invoke.return_value = workflow_result
        
        result = executor.execute(location_name="大阪")
        
        assert result['success'] is False
        assert result['error'] == "エラー1; エラー2"
        assert result['retry_count'] == 3
    
    def test_execute_exception(self, executor, mock_workflow):
        """例外発生時のテスト"""
        mock_workflow.invoke.side_effect = Exception("ワークフロー例外")
        
        with patch('src.workflows.workflow_executor.logger') as mock_logger:
            result = executor.execute(location_name="名古屋")
            mock_logger.error.assert_called()
        
        assert result['success'] is False
        assert 'error' in result
        assert result['execution_time_ms'] == 0