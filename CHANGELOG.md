# 📋 CHANGELOG

MobileCommentGeneratorの変更履歴

すべての重要な変更はこのファイルに文書化されます。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)に準拠し、
このプロジェクトは[Semantic Versioning](https://semver.org/lang/ja/)を採用しています。

## [Unreleased]

### Added
- ドキュメントを機能別に分割（architecture.md, deployment.md, frontend-guide.md, api-guide.md, development.md）
- 各ドキュメントファイルに関連ドキュメントへのナビゲーションセクションを追加
- CHANGELOG.mdファイルを新規作成

### Changed
- README.mdを簡潔化し、詳細情報を専門ドキュメントへ移動
- GitHub Issuesリンクを実際のリポジトリURLに修正

## [1.1.5] - 2024-12-XX

### Added
- 重複コメント防止機能：完全同一・類似表現の自動検出と代替選抜
- 天気優先順位ルール：雨・雪・雷を最優先、気温35℃以上で熱中症警戒
- 適応的コメント選抜：LLMによる天気状況に基づく最適なコメント選択
- タイムゾーン対応：JST時刻での翌朝9:00-18:00の天気予報に基づく生成

## [1.1.4] - 2024-11-XX

### Added
- React版フロントエンドの実装
- pnpmワークスペースによるモノレポ構成
- Storybookコンポーネントカタログ

### Changed
- 依存関係管理をpnpmに移行
- フロントエンドをNuxt.js + Reactのデュアル構成に

## [1.1.3] - 2024-10-XX

### Added
- FastAPI RESTful APIの実装
- Nuxt.js 3フロントエンドの実装
- 天気予報キャッシュ機能

### Changed
- バックエンドとフロントエンドの分離
- UIをStreamlitからNuxt.jsへ移行（Streamlitは開発用として保持）

## [1.1.2] - 2024-09-XX

### Added
- LangGraphワークフローの実装
- マルチLLMプロバイダー対応（OpenAI/Gemini/Anthropic）
- エラーハンドリングロジックの体系化

### Changed
- コメント生成ロジックをLangGraphベースに刷新
- 状態管理の改善

## [1.1.1] - 2024-08-XX

### Added
- 12時間周期天気予報のサポート
- 表現ルール遵守機能（NG表現禁止・値域制限・文字数規制）

### Fixed
- 天気データ取得の安定性向上

## [1.1.0] - 2024-07-XX

### Added
- ローカルCSVからの適応性ベース選抜機能
- Streamlit UIの実装

### Changed
- 天気コメント生成アルゴリズムの改良

## [1.0.0] - 2024-06-XX

### Added
- 初回リリース
- 基本的な天気予報に基づくコメント生成機能
- WxTech API統合
- OpenAI GPT連携

---

[Unreleased]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.5...HEAD
[1.1.5]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/sakamo-wni/MobileCommentGenerator/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/sakamo-wni/MobileCommentGenerator/releases/tag/v1.0.0