# クリーンアップ候補ファイル

## 削除可能なデッドコード

### 1. 未使用の非同期ワークフロー
- `/src/workflows/comment_generation_workflow.py`
  - `create_comment_generation_workflow_async()` 関数（削除済み）
  - 依存する未定義関数：
    - `get_messages_node`
    - `generate_comment_with_constraints_node`
    - `output_result_node`

### 2. バックアップファイル
- `/shared/src/composables/useLocationSelection.ts.bak`
- `/src/data/location_manager.py.bak`

### 3. 非推奨ファイル（ただし、まだ使用中のため削除不可）
これらのファイルは非推奨とマークされていますが、まだ多くの場所で使用されているため、削除できません：

- `/src/config/unified_config.py` - まだ多くのインポートで使用
- `/src/config/app_config.py` - CommentGenerationControllerなどで使用
- `/src/utils/weather_comment_validator.py` - 複数のノードで使用
- `/src/data/location_manager.py` - coastal_validatorで使用
- `/src/config/weather_settings.py` - 互換性のため維持
- `/src/config/app_settings.py` - 互換性のため維持

### 4. 未実装のTODO
- `/src/ui/pages/statistics.py` - `today_count = 0  # TODO: 実装`

## リファクタリングの成果

### 実装済みの改善
1. **LRUキャッシュの実装** - メモリ使用量の最適化
2. **CPU最適化** - 動的な並列処理ワーカー数の設定
3. **責務分離**：
   - `HistoryManager` - 履歴管理
   - `ConfigManager` - 設定管理
   - `RefactoredCommentGenerationController` - 責務を適切に分離
4. **巨大関数の分割**：
   - `WorkflowExecutor` - ワークフロー実行管理
   - `WorkflowStateBuilder` - 初期状態構築
   - `WorkflowResultParser` - 結果解析
   - `WorkflowResponseBuilder` - レスポンス構築

### 新規作成ファイル
- `/src/repositories/lru_comment_cache.py`
- `/src/repositories/optimized_comment_repository.py`
- `/src/utils/cpu_optimizer.py`
- `/src/controllers/history_manager.py`
- `/src/controllers/config_manager.py`
- `/src/controllers/refactored_comment_generation_controller.py`
- `/src/workflows/workflow_executor.py`
- `/src/workflows/refactored_comment_generation_workflow.py`

これらの改善により、コードの保守性、パフォーマンス、拡張性が向上しました。