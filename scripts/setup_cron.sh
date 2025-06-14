#!/bin/bash
# データクリーンアップのcronジョブを設定するスクリプト
# 
# 使用方法:
#   chmod +x scripts/setup_cron.sh
#   ./scripts/setup_cron.sh

# プロジェクトのルートディレクトリを取得
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ログディレクトリを作成
mkdir -p "$PROJECT_ROOT/logs"

# cronジョブのコマンド
CRON_COMMAND="cd $PROJECT_ROOT && /usr/bin/python3 scripts/cleanup_data.py >> logs/cleanup.log 2>&1"

# 現在のcrontabを一時ファイルに保存
crontab -l > /tmp/current_cron 2>/dev/null || true

# 既存のクリーンアップジョブを削除（重複防止）
grep -v "cleanup_data.py" /tmp/current_cron > /tmp/new_cron || true

# 新しいジョブを追加（毎日午前3時に実行）
echo "0 3 * * * $CRON_COMMAND" >> /tmp/new_cron

# 新しいcrontabを設定
crontab /tmp/new_cron

# 一時ファイルを削除
rm -f /tmp/current_cron /tmp/new_cron

echo "データクリーンアップのcronジョブを設定しました。"
echo "実行時間: 毎日午前3時"
echo "ログファイル: $PROJECT_ROOT/logs/cleanup.log"
echo ""
echo "現在のcrontab:"
crontab -l | grep cleanup_data.py || echo "（クリーンアップジョブが見つかりません）"