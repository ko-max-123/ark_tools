# -*- coding: utf-8 -*-
"""
Arknights リクルートタグ解析ツール
テンプレートマッチングによる画像検索
"""

import cv2
import numpy as np
from PIL import Image, ImageGrab, ImageEnhance
import datetime
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 文字エンコーディングを明示的に設定
import locale
import codecs

# Windows環境での文字エンコーディング問題を解決
if sys.platform.startswith('win'):
    # 標準出力と標準エラーのエンコーディングをUTF-8に設定
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    # 環境変数でUTF-8を強制
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # ロケール設定をUTF-8に変更
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass  # デフォルトロケールを使用

# Tesseractのパスを設定
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# タグリスト（高頻度順に並べ替え）
tags = ["先鋒タイプ", "前衛タイプ", "狙撃タイプ", "重装タイプ", "医療タイプ", "補助タイプ", "術師タイプ", "特殊タイプ", "近距離", "遠距離", "火力", "防御", "COST回復", "範囲攻撃", "生存", "治療", "支援", "弱化", "減速", "強制移動", "牽制", "爆発力", "召喚", "高速再配置", "初期", "ロボット", "元素", "エリート", "上級エリート"]

# グローバル変数
screenshot = None

# 高頻度タグの優先順位（実際の使用頻度に基づいて調整）
HIGH_PRIORITY_TAGS = [
    "前衛タイプ", "狙撃タイプ", "重装タイプ", "医療タイプ", "術師タイプ",
    "火力", "防御", "生存", "COST回復", "範囲攻撃"
]

# 募集条件部分を切り抜き (3段中2段目を切り抜く)
def crop_recruitment_area(image):
    height, width = image.shape[:2]
    cropped_img = image[height // 3 : 2 * height // 3, :]  # 高さの2段目部分を切り抜く
    cv2.imwrite("cropped_image.png", cropped_img)  # 一時ファイルとして保存
    return cropped_img

# ウィンドウサイズチェック機能
def check_window_size(image):
    """ウィンドウサイズが適切かチェックし、推奨サイズを提案"""
    height, width = image.shape[:2]
    
    # 最小推奨サイズ
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    RECOMMENDED_WIDTH = 1024
    RECOMMENDED_HEIGHT = 768
    
    print(f"現在のウィンドウサイズ: {width}x{height}")
    
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        print(f"⚠️  警告: ウィンドウサイズが小さすぎます")
        print(f"   現在: {width}x{height}")
        print(f"   最小推奨: {MIN_WIDTH}x{MIN_HEIGHT}")
        print(f"   推奨サイズ: {RECOMMENDED_WIDTH}x{RECOMMENDED_HEIGHT}")
        print(f"   パターンマッチングの精度が低下する可能性があります")
        return False, "small"
    elif width < RECOMMENDED_WIDTH or height < RECOMMENDED_HEIGHT:
        print(f"📱 注意: ウィンドウサイズがやや小さいです")
        print(f"   現在: {width}x{height}")
        print(f"   推奨サイズ: {RECOMMENDED_WIDTH}x{RECOMMENDED_HEIGHT}")
        print(f"   より良い結果を得るためにウィンドウサイズを大きくすることを推奨します")
        return True, "medium"
    else:
        print(f"✅ ウィンドウサイズは適切です: {width}x{height}")
        return True, "good"
    
    return True, "unknown"

# 小さいウィンドウ用の画像前処理関数
def preprocess_image_for_small_windows(image):
    """小さいウィンドウでも認識できるように画像を前処理"""
    try:
        # 画像のサイズを確認
        height, width = image.shape[:2]
        print(f"前処理前の画像サイズ: {width}x{height}")
        
        # 小さいウィンドウの場合は拡大処理
        if width < 800 or height < 600:
            # 2倍に拡大（より詳細な特徴を保持）
            scale_factor = 2.0
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            enlarged_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"小さいウィンドウを拡大: {width}x{height} -> {new_width}x{new_height}")
            image = enlarged_image
        
        # ノイズ除去（小さいウィンドウでも鮮明に）
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)
        
        # コントラスト強調（小さいウィンドウでも見やすく）
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # シャープニング（エッジを鮮明に）
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        print(f"前処理完了: 最終サイズ {sharpened.shape[1]}x{sharpened.shape[0]}")
        return sharpened
        
    except Exception as e:
        print(f"画像前処理でエラー: {e}")
        return image

def preprocess_template_for_small_windows(template):
    """小さいウィンドウ用のテンプレート前処理"""
    try:
        # テンプレートのサイズを確認
        height, width = template.shape[:2]
        print(f"テンプレート前処理前のサイズ: {width}x{height}")
        
        # 小さいテンプレートの場合は拡大処理
        if width < 50 or height < 50:
            scale_factor = 1.5
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            enlarged_template = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"小さいテンプレートを拡大: {width}x{height} -> {new_width}x{new_height}")
            template = enlarged_template
        
        # ノイズ除去
        denoised = cv2.fastNlMeansDenoisingColored(template, None, 2, 2, 5, 15)
        
        # コントラスト強調
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4,4))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        print(f"テンプレート前処理完了: 最終サイズ {enhanced.shape[1]}x{enhanced.shape[0]}")
        return enhanced
        
    except Exception as e:
        print(f"テンプレート前処理でエラー: {e}")
        return template

# 解像度調整処理
def adjust_resolution(image, target_dpi=300):
    scale_factor = target_dpi / 96
    width = int(image.shape[1] * scale_factor)
    height = int(image.shape[0] * scale_factor)
    return cv2.resize(image, (width, height))

# マッチング設定（小さいウィンドウでも認識できるように調整）
MATCHING_THRESHOLD = 0.3  # 0.5から0.3に下げて、より柔軟な認識を可能に
SCALE_RANGE = [0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6]  # より広いスケール範囲
ROTATION_ANGLES = [-20, -15, -10, -5, 0, 5, 10, 15, 20]  # より広い回転角度

def find_template_in_image(template_path, image):
    """テンプレート画像が画像内に存在するかチェック（スコア付き）"""
    try:
        template = cv2.imread(template_path)
        if template is None:
            return 0.0
        
        # より柔軟なマッチング（閾値を下げる）
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # デバッグ情報
        print(f"テンプレート {os.path.basename(template_path)}: スコア {max_val:.3f}")
        
        return max_val
        
    except Exception as e:
        print(f"テンプレートマッチングでエラー: {e}")
        return 0.0

# 改善された高精度テンプレートマッチング（小さいウィンドウ対応）
def find_template_in_image_high_quality(template_path, image, tag_name):
    """改善された高精度テンプレートマッチング（小さいウィンドウ対応）"""
    try:
        template = cv2.imread(template_path)
        if template is None:
            return tag_name, 0.0
        
        # 画像の前処理（小さいウィンドウでも認識できるように改善）
        processed_image = preprocess_image_for_small_windows(image)
        processed_template = preprocess_template_for_small_windows(template)
        
        # 拡張マルチスケールマッチング（より広い範囲）
        scale_scores = []
        
        for scale in SCALE_RANGE:
            if scale != 1.0:
                h, w = processed_template.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                if new_h > 0 and new_w > 0:
                    scaled_template = cv2.resize(processed_template, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                else:
                    continue
            else:
                scaled_template = processed_template
            
            if scaled_template.shape[0] > processed_image.shape[0] or \
               scaled_template.shape[1] > processed_image.shape[1]:
                continue
            
            # 回転不変性（より広い角度範囲）
            rotation_scores = []
            
            for angle in ROTATION_ANGLES:
                if angle != 0:
                    M = cv2.getRotationMatrix2D((scaled_template.shape[1] / 2, scaled_template.shape[0] / 2), angle, 1)
                    rotated_template = cv2.warpAffine(scaled_template, M, (scaled_template.shape[1], scaled_template.shape[0]))
                else:
                    rotated_template = scaled_template
                
                # 複数マッチング手法（より柔軟な閾値）
                method_scores = []
                
                # TM_CCOEFF_NORMED（メイン手法）
                result1 = cv2.matchTemplate(processed_image, rotated_template, cv2.TM_CCOEFF_NORMED)
                min_val1, max_val1, min_loc1, max_loc1 = cv2.minMaxLoc(result1)
                method_scores.append(max_val1)
                
                # TM_CCORR_NORMED（補完的手法）
                try:
                    result2 = cv2.matchTemplate(processed_image, rotated_template, cv2.TM_CCORR_NORMED)
                    min_val2, max_val2, min_loc2, max_loc2 = cv2.minMaxLoc(result2)
                    method_scores.append(max_val2)
                except:
                    pass
                
                # TM_SQDIFF_NORMED（距離ベース）
                try:
                    result3 = cv2.matchTemplate(processed_image, rotated_template, cv2.TM_SQDIFF_NORMED)
                    min_val3, max_val3, min_loc3, max_loc3 = cv2.minMaxLoc(result3)
                    # 距離を類似度に変換
                    method_scores.append(1 - min_val3)
                except:
                    pass
                
                # 最高スコアを採用
                if method_scores:
                    rotation_scores.append(max(method_scores))
            
            # 回転角度での最高スコアを採用
            if rotation_scores:
                scale_scores.append(max(rotation_scores))
        
        if scale_scores:
            final_score = max(scale_scores)
            print(f"タグ '{tag_name}' の最終スコア: {final_score:.3f}")
            return tag_name, final_score
        else:
            return tag_name, 0.0
        
    except Exception as e:
        print(f"改善された高精度テンプレートマッチングでエラー: {e}")
        return tag_name, 0.0

# シンプルな前処理関数（最小限）
def preprocess_image_simple(image):
    """シンプルな画像前処理（グレースケール変換のみ）"""
    try:
        # グレースケール変換のみ
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray
    except Exception as e:
        print(f"シンプル前処理でエラー: {e}")
        return image

def preprocess_template_simple(template):
    """シンプルなテンプレート前処理（グレースケール変換のみ）"""
    try:
        # グレースケール変換のみ
        gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        return gray
    except Exception as e:
        print(f"シンプルテンプレート前処理でエラー: {e}")
        return template

# 高精度前処理関数
def preprocess_image_high_quality(image):
    """高精度画像前処理"""
    try:
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # ノイズ除去（5x5ガウシアンフィルタ）
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # ヒストグラム均等化（CLAHE使用）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        equalized = clahe.apply(denoised)
        
        # エッジ強調（シャープネス向上）
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(equalized, -1, kernel)
        
        return sharpened
        
    except Exception as e:
        print(f"高精度前処理でエラー: {e}")
        return image

def preprocess_template_high_quality(template):
    """高精度テンプレート前処理"""
    try:
        # グレースケール変換
        gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # ノイズ除去（3x3メディアンフィルタ）
        denoised = cv2.medianBlur(gray, 3)
        
        # エッジ検出（Sobel使用）
        sobelx = cv2.Sobel(denoised, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(denoised, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = cv2.magnitude(sobelx, sobely)
        normalized_gradient = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        return normalized_gradient
        
    except Exception as e:
        print(f"高精度テンプレート前処理でエラー: {e}")
        return template

# 元の高精度前処理関数（完全復元）
def preprocess_image_original_high_quality(image):
    """元の高精度画像前処理（完全復元）"""
    try:
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 元のノイズ除去（複数フィルタの組み合わせ）
        # 1. ガウシアンフィルタ
        gaussian = cv2.GaussianBlur(gray, (5, 5), 0)
        # 2. メディアンフィルタ
        median = cv2.medianBlur(gaussian, 3)
        # 3. バイラテラルフィルタ
        bilateral = cv2.bilateralFilter(median, 9, 75, 75)
        
        # 元のヒストグラム均等化（複数手法の組み合わせ）
        # 1. CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        equalized_clahe = clahe.apply(bilateral)
        # 2. 通常のヒストグラム均等化
        equalized_normal = cv2.equalizeHist(bilateral)
        # 3. 両方の結果を組み合わせ
        equalized = cv2.addWeighted(equalized_clahe, 0.7, equalized_normal, 0.3, 0)
        
        # 元のエッジ強調（複数手法の組み合わせ）
        # 1. シャープネス強化
        kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(equalized, -1, kernel_sharp)
        
        # 2. エッジ検出（Sobel）
        sobelx = cv2.Sobel(sharpened, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(sharpened, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = cv2.magnitude(sobelx, sobely)
        normalized_gradient = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # 3. エッジ検出（Laplacian）
        laplacian = cv2.Laplacian(sharpened, cv2.CV_64F)
        laplacian_abs = cv2.convertScaleAbs(laplacian)
        
        # 4. エッジ検出（Canny）
        canny = cv2.Canny(sharpened, 50, 150)
        
        # 5. 全てのエッジ情報を組み合わせ
        combined_edges = cv2.addWeighted(normalized_gradient, 0.4, laplacian_abs, 0.3, 0)
        combined_edges = cv2.addWeighted(combined_edges, 0.8, canny, 0.2, 0)
        
        # 6. 最終的な画像を組み合わせ
        final_image = cv2.addWeighted(sharpened, 0.6, combined_edges, 0.4, 0)
        
        return final_image
        
    except Exception as e:
        print(f"元の高精度前処理でエラー: {e}")
        return image

def preprocess_template_original_high_quality(template):
    """元の高精度テンプレート前処理（完全復元）"""
    try:
        # グレースケール変換
        gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # 元のノイズ除去
        denoised = cv2.medianBlur(gray, 3)
        
        # 元のエッジ検出（Sobel）
        sobelx = cv2.Sobel(denoised, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(denoised, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = cv2.magnitude(sobelx, sobely)
        normalized_gradient = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # 元のエッジ強調
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(normalized_gradient, -1, kernel)
        
        return sharpened
        
    except Exception as e:
        print(f"元の高精度テンプレート前処理でエラー: {e}")
        return template

# アダプティブ閾値計算
def calculate_adaptive_threshold(image, template_path):
    """アダプティブ閾値計算"""
    try:
        # 画像の品質指標を計算
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. コントラスト指標
        contrast_score = np.std(gray) / 255.0
        
        # 2. シャープネス指標（Laplacian分散）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_score = np.var(laplacian) / 1000.0
        sharpness_score = min(1.0, sharpness_score)
        
        # 3. エッジ密度指標
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # 総合品質スコア
        quality_score = (
            contrast_score * 0.4 +
            sharpness_score * 0.4 +
            edge_density * 0.2
        )
        
        # ベース閾値（品質に応じて調整）
        base_threshold = 0.70  # 70%をベース
        
        # 品質による調整（±0.15）
        quality_adjustment = (quality_score - 0.5) * 0.3
        final_threshold = base_threshold + quality_adjustment
        
        # 閾値の範囲を制限（0.55〜0.85）
        final_threshold = max(0.55, min(0.85, final_threshold))
        
        return final_threshold
        
    except Exception as e:
        print(f"アダプティブ閾値計算でエラー: {e}")
        return 0.70  # デフォルト値

# 元のテンプレート品質計算（完全復元）
def calculate_template_quality_original(template_path):
    """元のテンプレート品質計算（完全復元）"""
    try:
        template = cv2.imread(template_path)
        if template is None:
            return 0.5
        
        # グレースケール変換
        if len(template.shape) == 3:
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            gray = template.copy()
        
        # 1. テンプレートサイズ指標
        h, w = gray.shape
        size_score = min(1.0, (h * w) / (100 * 100))
        
        # 2. コントラスト指標
        contrast_score = np.std(gray) / 255.0
        
        # 3. エッジの明確性
        edges = cv2.Canny(gray, 50, 150)
        edge_clarity = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # 4. テンプレートの一意性（境界差分）
        border_diff = calculate_border_difference_original(gray)
        
        # 総合品質スコア（元の重み付け）
        quality_score = (
            size_score * 0.2 +
            contrast_score * 0.3 +
            edge_clarity * 0.3 +
            border_diff * 0.2
        )
        
        return quality_score
        
    except Exception as e:
        print(f"元のテンプレート品質計算でエラー: {e}")
        return 0.5

def calculate_border_difference_original(gray_image):
    """元の境界差分計算（完全復元）"""
    try:
        h, w = gray_image.shape
        
        # 境界部分を抽出
        border = np.concatenate([
            gray_image[0, :],      # 上辺
            gray_image[-1, :],     # 下辺
            gray_image[:, 0],      # 左辺
            gray_image[:, -1]      # 右辺
        ])
        
        # 内部部分を抽出（境界から2ピクセル内側）
        inner = gray_image[2:-2, 2:-2]
        
        # 境界と内部の平均値の差分
        border_mean = np.mean(border)
        inner_mean = np.mean(inner)
        
        # 差分を正規化（0.0〜1.0）
        diff = abs(border_mean - inner_mean) / 255.0
        
        return min(1.0, diff * 3)  # 元のスケーリング
        
    except Exception as e:
        print(f"元の境界差分計算でエラー: {e}")
        return 0.5

# 元のアダプティブ閾値計算（完全復元）
def calculate_adaptive_threshold(image, template_path):
    """元のアダプティブ閾値計算（完全復元）"""
    try:
        # 画像の品質指標を詳細に計算
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. コントラスト指標
        contrast_score = np.std(gray) / 255.0
        
        # 2. シャープネス指標（Laplacian分散）
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_score = np.var(laplacian) / 1000.0
        sharpness_score = min(1.0, sharpness_score)
        
        # 3. エッジ密度指標
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # 4. ノイズ指標
        noise_score = 1.0 - (np.std(cv2.GaussianBlur(gray, (3, 3), 0)) / np.std(gray))
        
        # 5. テンプレート品質指標
        template_quality = calculate_template_quality_original(template_path)
        
        # 総合品質スコア（元の重み付け）
        quality_score = (
            contrast_score * 0.25 +
            sharpness_score * 0.25 +
            edge_density * 0.2 +
            noise_score * 0.15 +
            template_quality * 0.15
        )
        
        # 元のベース閾値（品質に応じて調整）
        base_threshold = 0.85  # 85%をベース（元の設定）
        
        # 品質による調整（±0.20）
        quality_adjustment = (quality_score - 0.5) * 0.4
        final_threshold = base_threshold + quality_adjustment
        
        # 閾値の範囲を制限（0.65〜1.05）
        final_threshold = max(0.65, min(1.05, final_threshold))
        
        return final_threshold
        
    except Exception as e:
        print(f"元のアダプティブ閾値計算でエラー: {e}")
        return 0.85  # 元のデフォルト値

# マッチングモード選択（シンプル vs 高精度）
MATCHING_MODE = "simple"  # "simple" または "high_quality"

# 統合テンプレートマッチング関数
def find_template_in_image_fast(template_path, image, tag_name):
    """統合テンプレートマッチング（モード選択可能）"""
    if MATCHING_MODE == "high_quality":
        return find_template_in_image_high_quality(template_path, image, tag_name)
    else:
        return find_template_in_image_simple(template_path, image, tag_name)

# シンプルなテンプレートマッチング（基本版）
def find_template_in_image_simple(template_path, image, tag_name):
    """シンプルなテンプレートマッチング（基本版）"""
    try:
        template = cv2.imread(template_path)
        if template is None:
            return tag_name, 0.0
        
        # 最小限の前処理（グレースケール変換のみ）
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # 基本的なマッチング（単一手法、単一スケール）
        result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        return tag_name, max_val
        
    except Exception as e:
        print(f"シンプルテンプレートマッチングでエラー: {e}")
        return tag_name, 0.0

# 閾値取得関数（モード選択可能）
def get_threshold(image, template_path):
    """閾値を取得（モード選択可能）"""
    if MATCHING_MODE == "high_quality":
        return calculate_adaptive_threshold(image, template_path)
    else:
        return 0.75  # 固定閾値

# 画像前処理関数
def find_template_image(image_path):
    img = cv2.imread(image_path)
    img = crop_recruitment_area(img)

    cv2.imwrite("processed_image.png", img)
    return img  # NumPy配列の形式で返す


# Arknightsウィンドウキャプチャ（改善版）
def capture_arknights_window():
    """Arknightsウィンドウを検出してキャプチャ（改善版）"""
    global screenshot
    
    print("🔍 capture_arknights_window() 開始（改善版）")
    
    try:
        print("📸 Arknightsウィンドウを検出中...")
        
        # 方法1: Arknightsウィンドウを直接検出
        try:
            import win32gui
            import win32ui
            import win32con
            
            # Arknightsウィンドウを検索
            arknights_hwnd = None
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_text:  # 空のタイトルは除外
                        # より柔軟な検索パターン
                        search_patterns = [
                            'arknights', 'アークナイツ', '明日方舟',  # 完全一致
                            'ark', 'arknight',  # 部分一致
                            '明日', '方舟',  # 日本語部分一致
                            'mobile', 'mob',  # モバイル版
                            'emulator', 'bluestacks', 'nox', 'ldplayer'  # エミュレータ
                        ]
                        
                        window_text_lower = window_text.lower()
                        for pattern in search_patterns:
                            if pattern in window_text_lower:
                                windows.append((hwnd, window_text))
                                print(f"🔍 候補ウィンドウ発見: '{window_text}' (パターン: {pattern})")
                                break
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                print(f"🔍 検出されたウィンドウ: {windows}")
                
                # 最適なウィンドウを選択（サイズと状態を考慮）
                best_window = None
                best_score = -1
                
                for hwnd, window_title in windows:
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        x, y, right, bottom = rect
                        width = right - x
                        height = bottom - y
                        
                        # ウィンドウの状態をチェック
                        is_iconic = win32gui.IsIconic(hwnd)
                        is_minimized = win32gui.IsIconic(hwnd)
                        
                        # スコアリング（大きいウィンドウ、非最小化状態を優先）
                        score = 0
                        if width >= 800 and height >= 600:  # 最小サイズ要件
                            score += 10
                        if width >= 1024 and height >= 768:  # 推奨サイズ
                            score += 20
                        if width >= 1920 and height >= 1080:  # フルHD
                            score += 30
                        
                        if not is_iconic and not is_minimized:
                            score += 50  # 非最小化状態を大幅に加算
                        
                        # タイトルの完全性も考慮
                        if any(exact in window_title.lower() for exact in ['arknights', 'アークナイツ', '明日方舟']):
                            score += 25
                        
                        print(f"📊 ウィンドウ '{window_title}': サイズ={width}x{height}, 最小化={is_iconic}, スコア={score}")
                        
                        if score > best_score:
                            best_score = score
                            best_window = (hwnd, window_title)
                            
                    except Exception as e:
                        print(f"⚠️ ウィンドウ '{window_title}' の評価でエラー: {e}")
                        continue
                
                if best_window:
                    arknights_hwnd, window_title = best_window
                    print(f"✅ 最適なウィンドウを選択: {window_title} (スコア: {best_score})")
                else:
                    # フォールバック: 最初のウィンドウを使用
                    arknights_hwnd, window_title = windows[0]
                    print(f"⚠️ フォールバック: 最初のウィンドウを使用: {window_title}")
                
                # ウィンドウの位置とサイズを取得
                rect = win32gui.GetWindowRect(arknights_hwnd)
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y
                
                print(f"📐 ウィンドウ位置: x={x}, y={y}, width={width}, height={height}")
                
                # ウィンドウが最小化されている場合は復元
                if win32gui.IsIconic(arknights_hwnd):
                    print("🔄 最小化されたウィンドウを復元中...")
                    win32gui.ShowWindow(arknights_hwnd, win32con.SW_RESTORE)
                    time.sleep(0.5)  # 復元完了を待つ
                    rect = win32gui.GetWindowRect(arknights_hwnd)
                    x, y, right, bottom = rect
                    width = right - x
                    height = bottom - y
                    print(f"📐 復元後の位置: x={x}, y={y}, width={width}, height={height}")
                
                # ウィンドウを前面に表示
                win32gui.SetForegroundWindow(arknights_hwnd)
                time.sleep(0.3)  # 前面表示完了を待つ
                
                # ウィンドウ領域をキャプチャ
                try:
                    # ウィンドウのクライアント領域を取得
                    client_rect = win32gui.GetClientRect(arknights_hwnd)
                    client_x, client_y, client_right, client_bottom = client_rect
                    client_width = client_right - client_x
                    client_height = client_bottom - client_y
                    
                    print(f"📐 クライアント領域: width={client_width}, height={client_height}")
                    
                    # クライアント領域が小さすぎる場合は警告
                    if client_width < 400 or client_height < 300:
                        print(f"⚠️ クライアント領域が小さすぎます: {client_width}x{client_height}")
                        print("🔄 全画面キャプチャにフォールバックします")
                        raise Exception("クライアント領域が小さすぎます")
                    
                    # ウィンドウのクライアント領域をキャプチャ
                    screenshot = capture_window_region(arknights_hwnd, client_rect)
                    if screenshot:
                        print(f"✅ ウィンドウキャプチャ完了: {screenshot.size}")
                        
                        # キャプチャされた画像の品質チェック
                        if screenshot.size[0] < 400 or screenshot.size[1] < 300:
                            print(f"⚠️ キャプチャされた画像が小さすぎます: {screenshot.size}")
                            print("🔄 全画面キャプチャにフォールバックします")
                            raise Exception("キャプチャされた画像が小さすぎます")
                        
                        start_analysis()
                        return
                    else:
                        print("⚠️ ウィンドウキャプチャが失敗しました")
                        raise Exception("ウィンドウキャプチャが失敗しました")
                        
                except Exception as e:
                    print(f"⚠️ ウィンドウキャプチャでエラー: {e}")
                    print("🔄 全画面キャプチャにフォールバックします")
            
        except ImportError:
            print("⚠️ win32guiが利用できません。全画面キャプチャを使用します")
        except Exception as e:
            print(f"⚠️ ウィンドウ検出でエラー: {e}")
            print("🔄 全画面キャプチャにフォールバックします")
        
        # 方法2: 全画面キャプチャ（フォールバック）
        print("📸 全画面キャプチャを実行します...")
        screenshot = ImageGrab.grab()
        print(f"✅ 全画面キャプチャ完了: {screenshot.size}")
        
        # 解析を開始
        print("🔍 キャプチャ完了、解析を開始します...")
        start_analysis()
        print("✅ start_analysis() 完了")
        
    except Exception as e:
        print(f"❌ ウィンドウキャプチャでエラー: {e}")
        import traceback
        traceback.print_exc()
        print("🔄 エラーが発生しましたが、全画面キャプチャを試行します")
        
        try:
            # 全画面キャプチャ
            screenshot = ImageGrab.grab()
            print(f"✅ 全画面キャプチャ完了: {screenshot.size}")
            
            # 解析を開始
            start_analysis()
            print("✅ start_analysis() 完了（エラー後の再試行）")
        except Exception as e2:
            print(f"❌ 全画面キャプチャでもエラー: {e2}")
            import traceback
            traceback.print_exc()
            # エラーログに記録
            try:
                script_dir = os.environ.get('SCRIPT_DIR')
                if not script_dir:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                error_log_path = os.path.join(script_dir, "error_log.txt")
                with open(error_log_path, "a", encoding="utf-8") as error_file:
                    error_file.write(f"{datetime.datetime.now()}: 全画面キャプチャエラー - {e2}\n")
                    error_file.write(f"詳細: {traceback.format_exc()}\n")
            except:
                print("❌ エラーログの書き込みに失敗しました")
    
    print("🔍 capture_arknights_window() 終了")

def capture_window_region(hwnd, rect):
    """指定されたウィンドウの特定領域をキャプチャ"""
    try:
        import win32gui
        import win32ui
        import win32con
        import win32api
        
        # ウィンドウのデバイスコンテキストを取得
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        # ビットマップを作成
        saveBitMap = win32ui.CreateBitmap()
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        # ウィンドウの内容をコピー
        result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (x, y), win32con.SRCCOPY)
        
        if result:
            # ビットマップをPIL Imageに変換
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # リソースを解放
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return img
        else:
            print("⚠️ ビットマップのコピーに失敗しました")
            return None
            
    except Exception as e:
        print(f"❌ ウィンドウ領域キャプチャでエラー: {e}")
        return None

# 手動領域選択機能（無効化）
def capture_screen_area():
    """手動で画面の領域を選択してキャプチャ（無効化）"""
    print("手動領域選択は無効化されています")
    print("ウィンドウ指定によるキャプチャを使用してください")
    
    # 代わりにウィンドウキャプチャを試行
    capture_arknights_window()

# テキストレポートと画像の保存
def save_results(tags, text, df=None):
    """結果をファイルに保存"""
    try:
        # スクリプトのディレクトリを取得（環境変数から優先）
        script_dir = os.environ.get('SCRIPT_DIR')
        if not script_dir:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"スクリプトディレクトリ: {script_dir}")
        
        # テキストレポートを保存（絶対パス）
        report_path = os.path.join(script_dir, "report.txt")
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(text)
        
        # 画像ファイルに保存（絶対パス）
        if screenshot:
            image_path = os.path.join(script_dir, "report.png")
            screenshot.save(image_path)
        
        print(f"結果を保存しました: {report_path}")
        
    except Exception as e:
        print(f"結果の保存でエラー: {e}")
        error_log_path = os.path.join(script_dir, "error_log.txt")
        try:
            with open(error_log_path, "a", encoding="utf-8") as error_file:
                error_file.write(f"{datetime.datetime.now()}: 結果保存エラー - {e}\n")
        except:
            print("エラーログの書き込みに失敗しました")

# OCR解析処理（最適化版）
def analyze_image():
    global screenshot
    if screenshot is None:
        print("キャプチャされた画像がありません。")
        return [], ""
    
    start_time = time.time()
    print("高速テンプレートマッチングによる解析を開始します")
    
    # 処理済み画像を作成
    script_dir = os.environ.get('SCRIPT_DIR')
    if not script_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    processed_img_path = os.path.join(script_dir, "processed_image.png")
    
    if screenshot:
        screenshot.save(processed_img_path)
        print(f"処理済み画像を保存しました: {processed_img_path}")
    
    # 画像を読み込み
    captured_img = cv2.imread(processed_img_path)
    if captured_img is None:
        print("画像の読み込みに失敗しました")
        return [], ""
    
    # ウィンドウサイズチェック
    print("🔍 ウィンドウサイズをチェック中...")
    is_appropriate, size_status = check_window_size(captured_img)
    
    if not is_appropriate:
        print("⚠️  警告: ウィンドウサイズが小さすぎるため、パターンマッチングの精度が低下する可能性があります")
        print("   推奨: アークナイツのウィンドウサイズを800x600以上に設定してください")
    elif size_status == "medium":
        print("📱 注意: より良い結果を得るために、ウィンドウサイズを1024x768以上に設定することを推奨します")
    
    # テンプレートファイルの定義（高頻度順）
    template_files = []
    
    print("🔍 テンプレートファイルの照合を開始...")
    
    # 利用可能なファイル名を表示
    tag_img_dir = os.path.join(script_dir, "tag_img")
    available_files = os.listdir(tag_img_dir)
    print(f"📁 利用可能なファイル: {len(available_files)} 個")
    for i, file_name in enumerate(available_files[:10]):  # 最初の10個を表示
        print(f"  {i+1}. {file_name}")
    if len(available_files) > 10:
        print(f"  ... 他 {len(available_files) - 10} 個")
    
    # 手動でファイル名とタグ名の対応を定義
    manual_mapping = {
        "zenei.png": "前衛タイプ",
        "jyusou.png": "重装タイプ", 
        "hojyo.png": "補助タイプ",
        "sogeki.png": "狙撃タイプ",
        "senpou.png": "先鋒タイプ",
        "iryo.png": "医療タイプ",
        "jyutushi.png": "術師タイプ",
        "enkyori.png": "遠距離",
        "kinkyori.png": "近距離",
        "cost.png": "COST回復",
        "bougyo.png": "防御",
        "shoki.png": "初期",
        "karyoku.png": "火力",
        "seizon.png": "生存",
        "hani.png": "範囲攻撃",
        "gensoku.png": "減速",
        "kyousei.png": "強制移動",
        "kensei.png": "牽制",
        "shoukan.png": "召喚",
        "kousoku.png": "高速再配置",
        "robot.png": "ロボット",
        "elite.png": "エリート",
        "tokusyu.png": "特殊タイプ",
        "chiryou.png": "治療",
        "shien.png": "支援",
        "bakuhatsu.png": "爆発力",
        "jyakuka.png": "弱化"
    }
    
    print("🔍 手動マッピングを使用してテンプレートを検索...")
    
    # 手動マッピングを使用してテンプレートを追加
    for file_name, tag_name in manual_mapping.items():
        file_path = os.path.join(tag_img_dir, file_name)
        if os.path.exists(file_path):
            template_files.append((file_path, tag_name))
            print(f"✅ マッピング追加: '{file_name}' -> '{tag_name}'")
        else:
            print(f"❌ ファイル不存在: {file_path}")
    
    print(f"🔍 照合完了: {len(template_files)} 個のテンプレートが見つかりました")
    
    # テンプレートファイルが見つからない場合のフォールバック
    if not template_files:
        print("⚠️ テンプレートファイルが見つからないため、デフォルトリストを使用します")
        template_files = [
            ("tag_img/zenei.png", "前衛タイプ"),
            ("tag_img/jyusou.png", "重装タイプ"),
            ("tag_img/hojyo.png", "補助タイプ"),
            ("tag_img/sogeki.png", "狙撃タイプ"),
            ("tag_img/senpou.png", "先鋒タイプ"),
            ("tag_img/iryo.png", "医療タイプ"),
            ("tag_img/jyutushi.png", "術師タイプ"),
            ("tag_img/enkyori.png", "遠距離"),
            ("tag_img/kinkyori.png", "近距離"),
            ("tag_img/cost.png", "COST回復"),
            ("tag_img/bougyo.png", "防御"),
            ("tag_img/shoki.png", "初期"),
            ("tag_img/karyoku.png", "火力"),
            ("tag_img/seizon.png", "生存"),
            ("tag_img/hani.png", "範囲攻撃"),
            ("tag_img/gensoku.png", "減速"),
            ("tag_img/kyousei.png", "強制移動"),
            ("tag_img/kensei.png", "牽制"),
            ("tag_img/shoukan.png", "召喚"),
            ("tag_img/kousoku.png", "高速再配置"),
            ("tag_img/robot.png", "ロボット"),
            ("tag_img/elite.png", "エリート"),
            ("tag_img/tokusyu.png", "特殊タイプ")
        ]
        print(f"🔄 フォールバック: {len(template_files)} 個のテンプレートを設定")
    
    print(f"処理対象テンプレート数: {len(template_files)}")
    
    # 並列処理でテンプレートマッチング（修正版）
    template_scores = []
    
    print("🔍 テンプレートマッチングを開始...")
    
    try:
        # 並列処理を無効化し、順次処理に変更
        print("🔄 順次処理でテンプレートマッチングを実行...")
        
        # 全てのテンプレートファイルを処理してスコアを取得
        print(f"🔍 全{len(template_files)}個のテンプレートを処理中...")
        
        for i, (template_path, tag_name) in enumerate(template_files):
            print(f"🔍 処理中 ({i+1}/{len(template_files)}): {tag_name}")
            
            try:
                # テンプレートマッチングを実行
                tag_name, score = find_template_in_image_fast(template_path, captured_img, tag_name)
                
                # 小さいウィンドウ対応の閾値を設定
                if size_status == "small":
                    # 小さいウィンドウの場合は閾値を下げる
                    threshold = MATCHING_THRESHOLD * 0.7  # 0.3 * 0.7 = 0.21
                    print(f"小さいウィンドウ対応: 閾値を {threshold:.3f} に調整")
                elif size_status == "medium":
                    # 中程度のウィンドウの場合は閾値を少し下げる
                    threshold = MATCHING_THRESHOLD * 0.85  # 0.3 * 0.85 = 0.255
                    print(f"中程度ウィンドウ対応: 閾値を {threshold:.3f} に調整")
                else:
                    # 適切なサイズの場合は標準閾値
                    threshold = MATCHING_THRESHOLD
                    print(f"標準閾値: {threshold:.3f}")
                
                if score > threshold:  # 調整された閾値を使用
                    template_scores.append((tag_name, score))
                    print(f"✅ タグ検出: {tag_name} (スコア: {score:.3f}, 閾値: {threshold:.3f})")
                else:
                    print(f"❌ 閾値未満: {tag_name} (スコア: {score:.3f}, 閾値: {threshold:.3f})")
                    
            except Exception as e:
                print(f"❌ テンプレート処理エラー {tag_name}: {e}")
                continue
        
        print(f"🔍 全テンプレート処理完了: {len(template_scores)}個のタグが検出されました")
                    
    except Exception as e:
        print(f"❌ テンプレートマッチングでエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        # エラーが発生した場合は空の結果を返す
        template_scores = []
    
    # スコアでソート（高い順）
    template_scores.sort(key=lambda x: x[1], reverse=True)
    print(f"スコア順ソート結果: {template_scores}")
    
    # 上位5個のタグを選択（スコアベース）
    limited_tags = [tag for tag, score in template_scores[:5]]
    limited_text = "\n".join(limited_tags)
    
    print(f"制限後のタグ（上位5個、スコアベース）: {limited_tags}")
    print(f"制限後のテキスト: {limited_text}")
    
    # タグリストとの照合
    matched_tags = [tag for tag in tags if tag in limited_text]
    print(f"マッチしたタグ: {matched_tags}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"処理時間: {processing_time:.2f}秒")
    
    return matched_tags, limited_text

# 解析開始処理
def start_analysis():
    try:
        print(f"start_analysis関数が呼ばれました")
        print(f"screenshotの状態: {screenshot is not None}")
        
        if screenshot is None:
            print("screenshotがNoneのため、messageboxを表示します")
            # messagebox.showerror("エラー", "キャプチャされた画像がありません。") # tkinterを削除
            print("キャプチャされた画像がありません。")
            return
        
        print("analyze_image関数を呼び出します")
        extracted_tags, extracted_text = analyze_image()
        print(f"analyze_imageの結果: tags={extracted_tags}, text={extracted_text}")
        
        # 結果を保存
        save_results(extracted_tags, extracted_text)
        
        print("start_analysis関数が完了しました")
        
    except Exception as e:
        print(f"start_analysisでエラーが発生: {e}")
        # messagebox.showerror("エラー", str(e)) # tkinterを削除
        print(str(e))

# テスト用の関数
def test_capture():
    """テスト用のキャプチャ関数"""
    global screenshot
    try:
        print("テスト用キャプチャを実行します")
        
        # ダミー画像を作成（テスト用）
        dummy_img = Image.new('RGB', (800, 600), color='white')
        screenshot = dummy_img
        
        print("ダミー画像を作成しました")
        
        # 解析を開始
        start_analysis()
        
    except Exception as e:
        print(f"テスト用キャプチャでエラー: {e}")
        import traceback
        traceback.print_exc()

# メイン実行部分
if __name__ == "__main__":
    print("=" * 50)
    print("tag_analysis.py が実行されました")
    print("=" * 50)
    
    try:
        print("1. スクリプト開始")
        
        # ウィンドウ指定によるキャプチャを実行
        print("2. capture_arknights_window() を呼び出し")
        capture_arknights_window()
        print("3. ウィンドウ指定によるキャプチャが実行されました")
        
    except Exception as e:
        print(f"❌ メイン実行でエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        
        # エラーログに記録
        try:
            with open("error_log.txt", "a", encoding="utf-8") as error_file:
                error_file.write(f"{datetime.datetime.now()}: メイン実行エラー - {e}\n")
                error_file.write(f"詳細: {traceback.format_exc()}\n")
        except:
            print("エラーログの書き込みに失敗しました")
    
    print("4. スクリプト終了")
    print("=" * 50)
