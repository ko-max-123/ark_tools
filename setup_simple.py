#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Python Environment Setup Script
システムのPythonを使用してパッケージをインストール
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    """メイン処理"""
    print("=== 簡易Python環境セットアップ開始 ===")
    
    # 現在のディレクトリを取得
    current_dir = Path(__file__).parent
    
    # システムのPythonを確認
    python_exe = None
    pip_exe = None
    
    if platform.system().lower() == "windows":
        python_exe = "python"
        pip_exe = "pip"
    else:
        python_exe = "python3"
        pip_exe = "pip3"
    
    # Pythonの存在確認
    try:
        result = subprocess.run([python_exe, "--version"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ Pythonが見つかりました: {result.stdout.strip()}")
        else:
            print(f"❌ Pythonが見つかりません: {python_exe}")
            return 1
    except Exception as e:
        print(f"❌ Pythonの確認中にエラー: {e}")
        return 1
    
    # pipの存在確認
    try:
        result = subprocess.run([pip_exe, "--version"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ pipが見つかりました: {result.stdout.strip()}")
        else:
            print(f"❌ pipが見つかりません: {pip_exe}")
            return 1
    except Exception as e:
        print(f"❌ pipの確認中にエラー: {e}")
        return 1
    
    # requirements.txtからパッケージをインストール
    requirements_file = current_dir / "requirements.txt"
    if requirements_file.exists():
        print("必要なPythonパッケージをインストール中...")
        
        try:
            # エンコーディング問題を回避するため、環境変数を明示的に設定
            env = os.environ.copy()
            env.update({
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONUTF8': '1',
                'PYTHONLEGACYWINDOWSSTDIO': 'utf-8'
            })
            
            # パッケージを個別にインストール
            with open(requirements_file, 'r', encoding='utf-8') as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            for package in packages:
                print(f"インストール中: {package}")
                try:
                    result = subprocess.run(
                        [pip_exe, "install", package],
                        env=env,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                    if result.returncode == 0:
                        print(f"✅ {package} のインストールが完了")
                    else:
                        print(f"⚠️  {package} のインストールに失敗: {result.stderr}")
                except Exception as e:
                    print(f"⚠️  {package} のインストール中にエラー: {e}")
            
            print("✅ パッケージのインストールが完了しました")
            
        except Exception as e:
            print(f"❌ パッケージのインストールに失敗: {e}")
            return 1
    else:
        print(f"⚠️  requirements.txtが見つかりません: {requirements_file}")
    
    # ランチャースクリプトの作成
    print("ランチャースクリプトを作成中...")
    
    if platform.system().lower() == "windows":
        launcher_content = f'''@echo off
REM Python Environment Launcher
REM システムのPythonを使用

REM メインスクリプトを実行
"{python_exe}" "{current_dir}\\tag_analysis.py" %*
'''
        launcher_file = current_dir / "run_tag_analysis.bat"
    else:
        launcher_content = f'''#!/bin/bash
# Python Environment Launcher
# システムのPythonを使用

# メインスクリプトを実行
{python_exe} "{current_dir}/tag_analysis.py" "$@"
'''
        launcher_file = current_dir / "run_tag_analysis.sh"
        # 実行権限を付与
        launcher_file.chmod(0o755)
    
    try:
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        print(f"✅ ランチャースクリプトを作成: {launcher_file}")
    except Exception as e:
        print(f"❌ ランチャースクリプトの作成に失敗: {e}")
        return 1
    
    print("=== 簡易Python環境セットアップ完了 ===")
    print(f"使用するPython: {python_exe}")
    print(f"使用するpip: {pip_exe}")
    
    if platform.system().lower() == "windows":
        print("実行方法: run_tag_analysis.bat")
    else:
        print("実行方法: ./run_tag_analysis.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
