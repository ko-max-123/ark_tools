#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedded Python Environment Setup Script
実行環境にPythonと必要なパッケージを自動インストール
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path

class PythonEnvironmentSetup:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.python_dir = self.script_dir / "embedded_python"
        self.packages_dir = self.script_dir / "python_packages"
        
        # プラットフォーム別の設定
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_macos = self.platform == "darwin"
        self.is_linux = self.platform == "linux"
        
        # Python 3.8.10のダウンロードURL（より軽量で安定、Windows 7/8/10/11対応）
        self.python_version = "3.8.10"
        self.python_urls = {
            "windows": f"https://www.python.org/ftp/python/{self.python_version}/python-{self.python_version}-embed-amd64.zip",
            "linux": f"https://www.python.org/ftp/python/{self.python_version}/Python-{self.python_version}.tgz",
            "macos": f"https://www.python.org/ftp/python/{self.python_version}/python-{self.python_version}-macos11.pkg"
        }
    
    def download_file(self, url, filename):
        """ファイルをダウンロード"""
        print(f"ダウンロード中: {filename}")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"✅ ダウンロード完了: {filename}")
            return True
        except Exception as e:
            print(f"❌ ダウンロード失敗: {e}")
            return False
    
    def extract_archive(self, archive_path, extract_to):
        """アーカイブを展開"""
        print(f"展開中: {archive_path}")
        try:
            archive_str = str(archive_path)
            if archive_str.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_str.endswith('.tar.gz') or archive_str.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_to)
            print(f"✅ 展開完了: {extract_to}")
            return True
        except Exception as e:
            print(f"❌ 展開失敗: {e}")
            return False
    
    def setup_windows_python(self):
        """Windows用Python環境をセットアップ"""
        print("Windows用Python環境をセットアップ中...")
        
        # 埋め込みPythonのダウンロードと展開
        print("埋め込みPythonをダウンロード中...")
        python_zip = self.script_dir / f"python-{self.python_version}-embed-amd64.zip"
        if not python_zip.exists():
            if not self.download_file(self.python_urls["windows"], python_zip):
                return False
        
        if not self.extract_archive(python_zip, self.python_dir):
            return False
        
        # 埋め込みPython環境の設定ファイルを修正
        self._setup_embedded_python_config()
        
        # pipのダウンロードとセットアップ
        pip_script = self.python_dir / "Scripts" / "pip.exe"
        if not pip_script.exists():
            pip_dir = self.python_dir / "Scripts"
            pip_dir.mkdir(exist_ok=True)
            
            # Python 3.8用のget-pip.pyをダウンロード
            get_pip_url = "https://bootstrap.pypa.io/pip/3.8/get-pip.py"
            get_pip_file = self.script_dir / "get-pip.py"
            if self.download_file(get_pip_url, get_pip_file):
                # pipをインストール
                python_exe = self.python_dir / "python.exe"
                try:
                    env = os.environ.copy()
                    env.update({
                        'PYTHONIOENCODING': 'utf-8',
                        'PYTHONUTF8': '1',
                        'PYTHONLEGACYWINDOWSSTDIO': 'utf-8'
                    })
                    
                    # 埋め込みPython環境のPYTHONPATHを設定
                    site_packages = self.python_dir / "Lib" / "site-packages"
                    env['PYTHONPATH'] = str(site_packages)
                    
                    result = subprocess.run(
                        [str(python_exe), str(get_pip_file), "--no-warn-script-location"],
                        env=env,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    if result.returncode == 0:
                        print("✅ pipのインストールが完了しました")
                    else:
                        print(f"⚠️  pipのインストールに失敗: {result.stderr}")
                        
                except Exception as e:
                    print(f"⚠️  pipのインストール中にエラー: {e}")
                
                # 一時ファイルを削除
                try:
                    get_pip_file.unlink()
                except:
                    pass
        
        return True
    
    def _setup_embedded_python_config(self):
        """埋め込みPython環境の設定を修正"""
        print("埋め込みPython環境の設定を修正中...")
        
        # python38._pthファイルを修正してsite-packagesを有効化
        pth_file = self.python_dir / f"python{self.python_version.split('.')[0]}{self.python_version.split('.')[1]}._pth"
        if pth_file.exists():
            try:
                with open(pth_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # コメントアウトされた行を有効化
                new_lines = []
                for line in lines:
                    if line.strip().startswith('#') and 'site-packages' in line:
                        new_lines.append(line[1:])  # コメントを削除
                    else:
                        new_lines.append(line)
                
                # 新しい行を追加
                new_lines.append('Lib\\site-packages\n')
                new_lines.append('Scripts\n')
                
                with open(pth_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print("✅ 埋め込みPython環境の設定を修正しました")
            except Exception as e:
                print(f"⚠️  設定ファイルの修正に失敗: {e}")
        
        # site-packagesディレクトリを作成
        site_packages_dir = self.python_dir / "Lib" / "site-packages"
        site_packages_dir.mkdir(parents=True, exist_ok=True)
        
        # 空の__init__.pyファイルを作成
        init_file = site_packages_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
    
    def setup_linux_python(self):
        """Linux用Python環境をセットアップ"""
        print("Linux用Python環境をセットアップ中...")
        
        # システムのPythonを使用（通常は存在する）
        python_exe = shutil.which("python3") or shutil.which("python")
        if python_exe:
            print(f"✅ システムPythonを使用: {python_exe}")
            return True
        
        # システムにPythonがない場合はダウンロード
        python_tar = self.script_dir / f"Python-{self.python_version}.tgz"
        if not python_tar.exists():
            if not self.download_file(self.python_urls["linux"], python_tar):
                return False
        
        if not self.extract_archive(python_tar, self.script_dir):
            return False
        
        # ソースからビルド（簡略化）
        print("⚠️  Linuxではシステムパッケージマネージャーを使用することを推奨")
        return False
    
    def setup_macos_python(self):
        """macOS用Python環境をセットアップ"""
        print("macOS用Python環境をセットアップ中...")
        
        # システムのPythonを使用（通常は存在する）
        python_exe = shutil.which("python3") or shutil.which("python")
        if python_exe:
            print(f"✅ システムPythonを使用: {python_exe}")
            return True
        
        print("⚠️  macOSではHomebrewを使用してPythonをインストールすることを推奨")
        return False
    
    def install_packages(self):
        """必要なPythonパッケージをインストール"""
        print("必要なPythonパッケージをインストール中...")
        
        # 埋め込みPython環境を使用
        if self.is_windows and (self.python_dir / "python.exe").exists():
            python_exe = self.python_dir / "python.exe"
            pip_exe = self.python_dir / "Scripts" / "pip.exe"
        else:
            python_exe = shutil.which("python3") or shutil.which("python")
            pip_exe = shutil.which("pip3") or shutil.which("pip")
        
        if not python_exe or not pip_exe:
            print("❌ Pythonまたはpipが見つかりません")
            return False
        
        # requirements.txtからパッケージをインストール
        requirements_file = self.script_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                # 環境変数を設定
                env = os.environ.copy()
                env.update({
                    'PYTHONIOENCODING': 'utf-8',
                    'PYTHONUTF8': '1',
                    'PYTHONLEGACYWINDOWSSTDIO': 'utf-8'
                })
                
                # 埋め込みPython環境の場合は、PYTHONPATHを設定
                if self.is_windows and (self.python_dir / "python.exe").exists():
                    site_packages = self.python_dir / "Lib" / "site-packages"
                    env['PYTHONPATH'] = str(site_packages)
                
                # パッケージを個別にインストール
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                for package in packages:
                    print(f"インストール中: {package}")
                    try:
                        # 埋め込みPython環境のpipを使用
                        if pip_exe.exists():
                            pip_cmd = [str(pip_exe), "install", package, "--target", str(site_packages), "--no-user"]
                        else:
                            print(f"⚠️  埋め込みpipが見つからないため、{package} をスキップ")
                            continue
                        
                        result = subprocess.run(
                            pip_cmd,
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
                return True
            except Exception as e:
                print(f"❌ パッケージのインストールに失敗: {e}")
                return False
        
        return True
    
    def create_launcher_script(self):
        """Pythonスクリプトを実行するためのランチャースクリプトを作成"""
        print("ランチャースクリプトを作成中...")
        
        if self.is_windows:
            launcher_content = f'''@echo off
REM Python Environment Launcher
set PYTHONPATH={self.python_dir}\\Lib\\site-packages
set PATH={self.python_dir};{self.python_dir}\\Scripts;%PATH%

REM メインスクリプトを実行
"{self.python_dir}\\python.exe" "{self.script_dir}\\tag_analysis.py" %*
'''
            launcher_file = self.script_dir / "run_tag_analysis.bat"
        else:
            launcher_content = f'''#!/bin/bash
# Python Environment Launcher
export PYTHONPATH={self.python_dir}/lib/python3.9/site-packages
export PATH={self.python_dir}/bin:$PATH

# メインスクリプトを実行
python3 "{self.script_dir}/tag_analysis.py" "$@"
'''
            launcher_file = self.script_dir / "run_tag_analysis.sh"
            # 実行権限を付与
            launcher_file.chmod(0o755)
        
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        print(f"✅ ランチャースクリプトを作成: {launcher_file}")
        return True
    
    def setup(self):
        """メインセットアップ処理"""
        print("=== Python環境セットアップ開始 ===")
        
        try:
            # ディレクトリを作成
            self.python_dir.mkdir(exist_ok=True)
            self.packages_dir.mkdir(exist_ok=True)
            
            # プラットフォーム別のセットアップ
            if self.is_windows:
                if not self.setup_windows_python():
                    print("⚠️  Windows用Pythonセットアップに失敗しましたが、続行します")
            elif self.is_linux:
                if not self.setup_linux_python():
                    print("⚠️  Linux用Pythonセットアップに失敗しましたが、続行します")
            elif self.is_macos:
                if not self.setup_macos_python():
                    print("⚠️  macOS用Pythonセットアップに失敗しましたが、続行します")
            
            # パッケージのインストール（失敗しても続行）
            try:
                if not self.install_packages():
                    print("⚠️  パッケージのインストールに失敗しましたが、続行します")
            except Exception as e:
                print(f"⚠️  パッケージのインストール中にエラーが発生: {e}")
            
            # ランチャースクリプトの作成
            try:
                if not self.create_launcher_script():
                    print("⚠️  ランチャースクリプトの作成に失敗しましたが、続行します")
            except Exception as e:
                print(f"⚠️  ランチャースクリプトの作成中にエラーが発生: {e}")
            
            print("=== Python環境セットアップ完了 ===")
            print(f"Python環境: {self.python_dir}")
            print(f"パッケージ: {self.packages_dir}")
            
            if self.is_windows:
                print("実行方法: run_tag_analysis.bat")
            else:
                print("実行方法: ./run_tag_analysis.sh")
            
            return True
            
        except Exception as e:
            print(f"❌ セットアップ中に予期しないエラーが発生: {e}")
            return False

def main():
    """メイン関数"""
    setup = PythonEnvironmentSetup()
    if setup.setup():
        print("✅ セットアップが正常に完了しました")
        return 0
    else:
        print("❌ セットアップに失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())
