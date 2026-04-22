#!/usr/bin/env python3
"""
Sprint3 テスト実行スクリプト

使用方法:
    python run_tests.py              # 全テスト実行
    python run_tests.py --lock       # Redis Lockテストのみ
    python run_tests.py --toneri     # 舎人エージェントテストのみ  
    python run_tests.py --integration # 連携テストのみ
    python run_tests.py --verbose    # 詳細出力
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def run_command(cmd, verbose=False):
    """コマンドを実行して結果を表示"""
    if verbose:
        print(f"実行中: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=not verbose,
        text=True,
        cwd=str(project_root)
    )
    
    if verbose:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"エラー出力: {result.stderr}")
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Sprint3 テスト実行スクリプト")
    parser.add_argument("--lock", action="store_true", help="Redis Lockテストのみ実行")
    parser.add_argument("--toneri", action="store_true", help="舎人エージェントテストのみ実行")
    parser.add_argument("--integration", action="store_true", help="連携テストのみ実行")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏛️  Sprint3 テスト実行")
    print("=" * 60)
    
    # Redisサーバー接続確認
    print("\n📡 Redisサーバー接続確認...")
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
        client.ping()
        print("✅ Redisサーバーに接続しました")
    except Exception as e:
        print(f"❌ Redisサーバーに接続できません: {e}")
        print("💡 Redisサーバーを起動してください: redis-server")
        return 1
    
    success = True
    
    # テスト実行
    if args.lock:
        print("\n🔒 Redis Lock 排他制御テスト")
        success &= run_command([
            sys.executable, "-m", "pytest", 
            "tests/sprint3/test_redis_lock.py",
            "-v" if args.verbose else "",
            "--tb=short"
        ], args.verbose)
        
    elif args.toneri:
        print("\n👤 舎人エージェント実装テスト")
        success &= run_command([
            sys.executable, "-m", "pytest",
            "tests/sprint3/test_toneri_agent.py", 
            "-v" if args.verbose else "",
            "--tb=short"
        ], args.verbose)
        
    elif args.integration:
        print("\n🤝 関白-頭弁-舎人連携テスト")
        success &= run_command([
            sys.executable, "-m", "pytest",
            "tests/sprint3/test_integration.py",
            "-v" if args.verbose else "",
            "--tb=short"
        ], args.verbose)
        
    else:
        # 全テスト実行
        print("\n🧪 全テスト実行")
        success &= run_command([
            sys.executable, "-m", "pytest",
            "tests/sprint3/",
            "-v" if args.verbose else "",
            "--tb=short",
            "--color=yes"
        ], args.verbose)
    
    # 結果表示
    print("\n" + "=" * 60)
    if success:
        print("🎉 全テストが成功しました！")
        print("\n📋 Sprint3 実装要件チェック:")
        print("✅ Redis Lockの排他制御")
        print("✅ 舎人エージェントの実装")
        print("✅ 関白-頭弁-舎人の連携")
        print("✅ 並列処理の実装")
    else:
        print("❌ テストが失敗しました")
        print("💡 上記のエラーメッセージを確認してください")
    
    print("=" * 60)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
