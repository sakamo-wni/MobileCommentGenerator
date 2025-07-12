"""実際のアプリケーションのパフォーマンステスト"""

import time
import subprocess
import requests
import os

def test_streamlit_startup():
    """Streamlitアプリの起動時間を測定"""
    print("=== Streamlitアプリの起動時間測定 ===\n")
    
    # 既存のプロセスを終了
    subprocess.run(["pkill", "-f", "streamlit run"], capture_output=True)
    time.sleep(1)
    
    # アプリを起動
    print("アプリを起動中...")
    start_time = time.time()
    
    process = subprocess.Popen(
        ["python", "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # アプリが起動するまで待機
    max_wait = 30  # 最大30秒待機
    check_interval = 0.5
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            response = requests.get("http://localhost:8501", timeout=1)
            if response.status_code == 200:
                startup_time = time.time() - start_time
                print(f"✓ アプリ起動完了: {startup_time:.2f}秒")
                break
        except:
            pass
        
        time.sleep(check_interval)
        elapsed += check_interval
    else:
        print(f"✗ アプリ起動タイムアウト（{max_wait}秒）")
        startup_time = None
    
    # プロセスを終了
    process.terminate()
    time.sleep(1)
    
    return startup_time

def test_generation_speed():
    """コメント生成の速度を測定（コントローラーのみ）"""
    print("\n=== コメント生成速度の測定 ===\n")
    
    # 環境変数を設定
    os.environ["LLM_PERFORMANCE_MODE"] = "true"
    os.environ["WXTECH_CACHE_TTL"] = "300"
    
    try:
        from src.controllers.comment_generation_controller import CommentGenerationController
        
        print("コントローラーを初期化中...")
        init_start = time.time()
        controller = CommentGenerationController()
        init_time = time.time() - init_start
        print(f"初期化時間: {init_time:.2f}秒")
        
        # テスト地点
        test_locations = ["東京"]
        
        for i, location in enumerate(test_locations):
            print(f"\n{i+1}. {location}:")
            
            start = time.time()
            try:
                result = controller.generate(location)
                elapsed = time.time() - start
                print(f"  生成時間: {elapsed:.2f}秒")
                
                if result:
                    print(f"  成功: {result.comment[:30]}...")
                else:
                    print(f"  失敗: 結果なし")
                    
            except Exception as e:
                elapsed = time.time() - start
                print(f"  エラー（{elapsed:.2f}秒）: {type(e).__name__}: {str(e)}")
                
    except Exception as e:
        print(f"初期化エラー: {type(e).__name__}: {str(e)}")

def main():
    """メイン処理"""
    print("実際のアプリケーションパフォーマンステスト")
    print("=" * 50)
    
    # Streamlit起動テスト
    startup_time = test_streamlit_startup()
    
    # コメント生成テスト
    test_generation_speed()
    
    print("\n\n=== 結果サマリー ===")
    if startup_time:
        print(f"Streamlit起動時間: {startup_time:.2f}秒")

if __name__ == "__main__":
    main()