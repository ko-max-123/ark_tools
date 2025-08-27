# Arktools - アークナイツ 募集条件解析ツール
エラー

## 概要
アークナイツの募集画面をキャプチャして、テンプレートマッチングにより自動的にタグを認識・解析するツールです。

## 特徴
- 画面キャプチャによる自動タグ認識
- **完全埋め込みPython環境**: システムにPythonがインストールされていなくても動作
- クロスプラットフォーム対応（Windows, macOS, Linux）
- 依存関係なしでの即座実行

## セットアップ

### 開発環境での実行
```bash
# 依存関係をインストール
npm install

# 埋め込みPython環境をセットアップ
npm run setup:python

# アプリを起動
npm start
```

### ビルドと配布
```bash
# Windows用にビルド
npm run build:win

# macOS用にビルド
npm run build:mac

# Linux用にビルド
npm run build:linux
```

## Python環境について

### 概要
このツールは、**完全埋め込みPython環境**を使用して動作します。システムにPythonがインストールされていなくても、必要な環境が自動的にセットアップされます。

### 含まれるもの
- **Python 3.8.10**: 軽量で安定した埋め込み環境
- **pip**: パッケージマネージャー
- **必要なパッケージ**:
  - `opencv-python==4.4.0.46` - 画像処理・テンプレートマッチング
  - `numpy==1.19.5` - 数値計算
  - `Pillow==8.0.1` - 画像操作
  - `pytesseract==0.3.10` - OCR機能

### セットアップの流れ
1. **セットアップ時**: `setup_embedded_python.py`が実行され、以下が自動構築される
   - Python 3.8.10の埋め込み環境をダウンロード
   - pipを自動インストール
   - 必要なPythonパッケージを自動インストール
   - 環境設定ファイルを最適化
2. **実行時**: 埋め込みPython環境を使用してPythonスクリプトを実行
3. **環境変数**: 埋め込み環境用の適切な環境変数が自動設定される

### プラットフォーム別の動作
- **Windows**: 埋め込みPython環境の`python.exe`を使用
- **macOS/Linux**: 埋め込みPython環境の`python3`を使用

## 使用方法

### アプリケーション経由
1. Electronアプリを起動
2. スクリーンショットボタンをクリック
3. タグ解析結果を確認

### 直接実行
埋め込みPython環境を直接使用：

```bash
# Windows
.\embedded_python\python.exe tag_analysis.py

# または
.\run_tag_analysis.bat
```

## トラブルシューティング

### セットアップエラーが発生する場合
```bash
# 既存の環境をクリアして再セットアップ
Remove-Item -Recurse -Force embedded_python
python setup_embedded_python.py
```

### パッケージが見つからないエラー
```bash
# 埋め込みpipを使用して個別インストール
.\embedded_python\Scripts\pip.exe install opencv-python==4.4.0.46 --target .\embedded_python\Lib\site-packages --no-user
```

### パフォーマンスの問題
- 初回起動時は埋め込みPython環境の初期化に時間がかかる場合があります
- 2回目以降は高速に起動します

## ファイル構成
```
ark_tools/
├── main.js                          # Electronメインプロセス
├── renderer.js                      # レンダラープロセス
├── index.html                       # メインUI
├── tag_analysis.py                  # Python解析スクリプト
├── setup_embedded_python.py         # 埋め込みPython環境セットアップ
├── requirements.txt                  # Python依存関係
├── embedded_python/                 # 埋め込みPython環境
│   ├── python.exe                   # Python実行ファイル
│   ├── Scripts/                     # pip等のスクリプト
│   └── Lib/site-packages/           # インストールされたパッケージ
├── tag_img/                         # タグテンプレート画像
├── package.json                     # プロジェクト設定
└── .gitignore                       # Git除外設定
```

## 開発者向け情報

### 埋め込みPython環境の確認
```bash
# Pythonバージョン確認
.\embedded_python\python.exe --version

# インストール済みパッケージ確認
.\embedded_python\Scripts\pip.exe list
```

### 新しいPythonパッケージを追加する場合
1. `requirements.txt`にパッケージ名とバージョンを追加
2. `setup_embedded_python.py`の`install_packages()`メソッドが自動的にインストール

### Pythonスクリプトを修正する場合
1. `tag_analysis.py`を編集
2. 必要に応じて`requirements.txt`を更新
3. アプリを再ビルド

## 技術仕様

### 埋め込みPython環境
- **Python 3.8.10**: Windows 7/8/10/11対応の軽量環境
- **自動設定**: `python38._pth`ファイルの自動最適化
- **site-packages**: パッケージインストール用ディレクトリの自動作成

### 環境変数
- `PYTHONPATH`: 埋め込み環境のsite-packages
- `PYTHONIOENCODING`: UTF-8
- `PYTHONUTF8`: 1
- `PYTHONLEGACYWINDOWSSTDIO`: UTF-8（Windows）

## ライセンス
MIT License

## サポート
問題が発生した場合は、以下の手順で対処してください：
1. ログファイル（`error_log.txt`）を確認
2. 埋め込みPython環境のセットアップを再実行
3. アプリを再ビルド
