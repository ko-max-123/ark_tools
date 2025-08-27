#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post Build Setup Script
ビルド後に埋め込みPython環境をセットアップ
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    """メイン処理"""
    print("=== ビルド後セットアップ開始 ===")
    
    # 現在のディレクトリを取得
    current_dir = Path(__file__).parent
    
    # 埋め込みPython環境のセットアップスクリプトを実行
    setup_script = current_dir / "setup_embedded_python.py"
    
    if not setup_script.exists():
        print(f"❌ セットアップスクリプトが見つかりません: {setup_script}")
        return 1
    
    try:
        # セットアップスクリプトを実行
        print("埋め込みPython環境をセットアップ中...")
        result = subprocess.run([sys.executable, str(setup_script)], 
                              cwd=current_dir, 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ セットアップが完了しました")
            print("出力:", result.stdout)
            return 0
        else:
            print("❌ セットアップに失敗しました")
            print("エラー:", result.stderr)
            return 1
            
    except Exception as e:
        print(f"❌ セットアップ実行中にエラーが発生: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
