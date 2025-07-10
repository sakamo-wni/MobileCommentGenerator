"""権限エラーのテスト"""

import os
import tempfile
from pathlib import Path

# 読み取り専用ディレクトリを作成
with tempfile.TemporaryDirectory() as tmpdir:
    readonly_dir = Path(tmpdir) / "readonly"
    readonly_dir.mkdir()
    
    # 読み取り専用に設定
    os.chmod(readonly_dir, 0o444)
    
    # 環境変数を設定
    os.environ["DATA_DIR"] = str(readonly_dir / "data")
    os.environ["CSV_DIR"] = str(readonly_dir / "csv")
    
    try:
        # AppSettingsをインポート（権限エラーが発生するはず）
        from src.config.settings.app_settings import AppSettings
        settings = AppSettings()
        print("✅ AppSettingsのインポートが成功しました（権限エラーは内部で処理されました）")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # 権限を戻す
        os.chmod(readonly_dir, 0o755)