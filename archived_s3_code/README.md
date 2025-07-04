# アーカイブされたS3関連コード

このディレクトリには、S3を使用していた旧実装のコードが保存されています。
現在のシステムは、ローカルCSVファイルを使用するように変更されました。

## アーカイブされたファイル

- `s3_comment_repository.py` - S3からコメントを取得する旧リポジトリ実装
- `test_s3_comment_repository.py` - S3リポジトリのテストコード
- `s3_comment_retrieval.md` - S3関連のドキュメント
- `enhanced_comment_generator.py` - S3を使用してCSVを強化する旧スクリプト

## 現在の実装

現在のシステムは以下のファイルを使用しています：

- `src/repositories/local_comment_repository.py` - ローカルCSVからコメントを読み込む
- `output/` ディレクトリ内の季節別CSVファイル

## 移行の理由

1. **依存関係の削減**: AWS SDK (boto3) への依存を削除
2. **シンプルな構成**: ローカルファイルのみで動作
3. **開発の容易性**: AWS認証情報の設定が不要
4. **パフォーマンス**: ローカルファイルアクセスの高速化

## 復元方法

S3実装を復元する必要がある場合：

1. `boto3` を requirements.txt と pyproject.toml に追加
2. このディレクトリのファイルを元の場所に戻す
3. テストを実行して動作を確認