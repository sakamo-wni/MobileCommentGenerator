"""
バリデーション型定義のテスト

Protocolベースの型チェックが正しく動作することを確認
"""

import pytest
from src.types.validation import (
    ValidationResult,
    DictValidationResult,
    ensure_validation_result,
)
from src.data.evaluation_criteria import EvaluationResult, CriterionScore
from src.workflows.comment_generation_workflow import should_retry


class TestValidationProtocol:
    """ValidationResultプロトコルのテスト"""

    def test_dict_validation_result(self):
        """辞書形式のバリデーション結果のテスト"""
        # 正常なケース
        data = {"is_valid": True}
        result = DictValidationResult(data)
        assert result.is_valid is True

        # エラーがある場合
        data = {"is_valid": False}
        result = DictValidationResult(data)
        assert result.is_valid is False

        # デフォルト値のテスト
        data = {}
        result = DictValidationResult(data)
        assert result.is_valid is True  # デフォルトはTrue

    def test_ensure_validation_result(self):
        """ensure_validation_result関数のテスト"""
        # None の場合
        assert ensure_validation_result(None) is None

        # 辞書の場合
        dict_result = {"is_valid": False}
        result = ensure_validation_result(dict_result)
        assert isinstance(result, DictValidationResult)
        assert result.is_valid is False

        # EvaluationResultオブジェクトの場合
        eval_result = EvaluationResult(
            is_valid=True,
            total_score=0.8,
            criterion_scores=[],
        )
        result = ensure_validation_result(eval_result)
        assert result is eval_result  # 同じオブジェクトが返される
        assert result.is_valid is True

        # Protocolに適合するカスタムオブジェクト
        class CustomValidation:
            @property
            def is_valid(self) -> bool:
                return False

        custom = CustomValidation()
        result = ensure_validation_result(custom)
        assert result is custom
        assert result.is_valid is False

    def test_protocol_compliance(self):
        """ValidationResultプロトコルへの適合性テスト"""
        # DictValidationResultがProtocolに適合することを確認
        dict_val = DictValidationResult({"is_valid": True})
        assert isinstance(dict_val, ValidationResult)

        # EvaluationResultがProtocolに適合することを確認
        eval_result = EvaluationResult(
            is_valid=False,
            total_score=0.5,
            criterion_scores=[],
        )
        # EvaluationResultにis_validプロパティがあることを確認
        assert hasattr(eval_result, "is_valid")
        assert isinstance(eval_result, ValidationResult)


class TestWorkflowIntegration:
    """ワークフローとの統合テスト"""

    def test_should_retry_with_dict(self):
        """should_retry関数が辞書形式で動作することを確認"""
        # リトライ不要のケース
        state = {"retry_count": 0, "validation_result": {"is_valid": True}}
        assert should_retry(state) == "continue"

        # リトライ必要のケース
        state = {"retry_count": 2, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "retry"

        # リトライ上限に達したケース
        state = {"retry_count": 5, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "continue"

    def test_should_retry_with_object(self):
        """should_retry関数がオブジェクト形式で動作することを確認"""
        # EvaluationResultオブジェクトを使用
        eval_result = EvaluationResult(
            is_valid=True,
            total_score=0.8,
            criterion_scores=[],
        )
        state = {"retry_count": 0, "validation_result": eval_result}
        assert should_retry(state) == "continue"

        # リトライ必要なケース
        eval_result = EvaluationResult(
            is_valid=False,
            total_score=0.3,
            criterion_scores=[],
        )
        state = {"retry_count": 2, "validation_result": eval_result}
        assert should_retry(state) == "retry"

    def test_should_retry_edge_cases(self):
        """should_retry関数のエッジケーステスト"""
        # validation_resultがNoneの場合
        state = {"retry_count": 0, "validation_result": None}
        assert should_retry(state) == "continue"

        # validation_resultが存在しない場合
        state = {"retry_count": 0}
        assert should_retry(state) == "continue"

        # 不正な形式のvalidation_result
        state = {"retry_count": 0, "validation_result": "invalid"}
        assert should_retry(state) == "continue"