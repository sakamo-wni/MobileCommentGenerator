# Manual Test Scripts

このディレクトリには手動テスト用のスクリプトが含まれています。

## スクリプト一覧

### test_unified_workflow.py
統合ワークフローの動作確認用スクリプト

```bash
python examples/manual_tests/test_unified_workflow.py
```

### test_api_unified.py
API経由での統合ワークフローテスト

```bash
python examples/manual_tests/test_api_unified.py
```

### test_workflow_direct.py
ワークフローの直接実行テスト

```bash
python examples/manual_tests/test_workflow_direct.py
```

### test_workflow_performance.py
パフォーマンス測定用スクリプト

```bash
python examples/manual_tests/test_workflow_performance.py
```

### test_shower_rain_fix.py
にわか雨修正の動作確認

```bash
python examples/manual_tests/test_shower_rain_fix.py
```

## 注意事項

これらのスクリプトは開発時の動作確認用です。正式なテストは `tests/` ディレクトリ内のユニットテストを使用してください。