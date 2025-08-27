#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arktools Python環境セットアップスクリプト
必要なPythonパッケージをインストールします
"""

import subprocess
import sys
import os

def install_package(package):
    """パッケージをインストール"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} のインストールが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} のインストールに失敗しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 Arktools Python環境セットアップを開始します...")
    
    # 必要なパッケージリスト
    required_packages = [
        "opencv-python",
        "pillow",
        "numpy",
        "pywin32"
    ]
    
    print(f"📦 インストール対象パッケージ: {', '.join(required_packages)}")
    
    # 各パッケージをインストール
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 インストール結果: {success_count}/{len(required_packages)} パッケージが成功")
    
    if success_count == len(required_packages):
        print("🎉 すべてのパッケージのインストールが完了しました！")
        print("Arktoolsを使用する準備が整いました。")
    else:
        print("⚠️ 一部のパッケージのインストールに失敗しました。")
        print("手動でインストールするか、管理者権限で実行してください。")
    
    # ユーザーにEnterキーを待つ
    input("\nEnterキーを押して終了してください...")

if __name__ == "__main__":
    main()
