from pywinauto import Desktop
import win32gui
import win32con
from pywinauto import Application
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image
import datetime
#import pytesseract
import cv2
import numpy as np
import re
import os
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # ピクセル制限解除

# Tesseractのパスを設定
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# タグリスト
tags = ["先鋒タイプ", "前衛タイプ", "狙撃タイプ", "重装タイプ", "医療タイプ", "補助タイプ", "術師タイプ", "特殊タイプ", "近距離", "遠距離", "火力", "防御", "COST回復", "範囲攻撃", "生存", "治療", "支援", "弱化", "減速", "強制移動", "牽制", "爆発力", "召喚", "高速再配置", "初期", "ロボット", "元素", "エリート", "上級エリート"]

# グローバル変数
global screenshot
screenshot = None

# リソースディレクトリのパスを取得
def resource_path(relative_path):
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 募集条件部分を切り抜き (3段中2段目を切り抜く)
def crop_recruitment_area(image):
    height, width = image.shape[:2]
    cropped_img = image[height // 3 : 2 * height // 3, :]  # 高さの2段目部分を切り抜く
    cv2.imwrite(resource_path("resources/cropped_image.png"), cropped_img)  # 一時ファイルとして保存
    return cropped_img

# 解像度調整処理
def adjust_resolution(image, target_dpi=300):
    scale_factor = target_dpi / 96
    width = int(image.shape[1] * scale_factor)
    height = int(image.shape[0] * scale_factor)
    return cv2.resize(image, (width, height))

# テンプレートマッチングによる画像検索
def find_template_in_image(template_path, target_image):
    template = cv2.imread(template_path, 0)
    if template is None:
        print(f"テンプレート画像が見つかりません: {template_path}")
        return False
    target_image_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)  # 明示的にグレースケールに変換

    # テンプレート画像がターゲット画像よりも大きい場合、テンプレート画像をターゲット画像に合わせてリサイズ
    if template.shape[0] > target_image_gray.shape[0] or template.shape[1] > target_image_gray.shape[1]:
        scale_factor = min(target_image_gray.shape[0] / template.shape[0], target_image_gray.shape[1] / template.shape[1])
        template = cv2.resize(template, (int(template.shape[1] * scale_factor), int(template.shape[0] * scale_factor)))

    res = cv2.matchTemplate(target_image_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val >= 0.9  # 類似度80%以上を検出基準とする

# 画像前処理関数
def find_template_image(image_path):
    img = cv2.imread(image_path)
    img = crop_recruitment_area(img)

    cv2.imwrite(resource_path("resources/processed_image.png"), img)
    return img  # NumPy配列の形式で返す

# アークナイツウィンドウキャプチャ
from pywinauto import Desktop

def capture_window():
    global screenshot
    try:
        app = Desktop(backend="uia").window(title_re=".*アークナイツ.*")
        app.set_focus()  # ウィンドウをフォーカス
        
        # ウィンドウハンドルを取得
        hwnd = app.wrapper_object().handle
        
        # ウィンドウをメイン画面に移動
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)

        # ウィンドウを最大化
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

        # ウィンドウの位置とサイズを再取得
        rect = app.rectangle()
        
        # キャプチャを取得
        screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        screenshot.save(resource_path("resources/captured_image.png"))
        
        # キャプチャ後の処理を実行
        start_analysis()
    except Exception as e:
        error_message = f"解析中にエラーが発生しました: {e}"
        print(error_message)  # コンソールにエラーメッセージを出力
        with open(resource_path("resources/error_log.txt"), "a", encoding="utf-8") as error_file:
            error_file.write(f"{datetime.datetime.now()}: {error_message}\n")

# テキストレポートと画像の保存
def save_results(df, extracted_text):
    global screenshot
    timestamp = datetime.datetime.now().strftime("%m%d%H%M")
    txt_path = resource_path("resources/report.txt")
    img_path = resource_path("resources/report.png")
    with open(txt_path, 'w', encoding='utf-8') as file:
        file.write(extracted_text)
    if screenshot:
        screenshot.save(img_path)

# OCR解析処理
def analyze_image():
    global screenshot
    if screenshot is None:
        messagebox.showerror("エラー", "キャプチャされた画像がありません。")
        return []
    processed_img_path = resource_path("resources/processed_image.png")
    processed_img = find_template_image(resource_path("resources/captured_image.png"))
    #extracted_text = pytesseract.image_to_string(
    #    Image.open(processed_img_path), lang='jpn', config='--psm 6 --oem 1 -c preserve_interword_spaces=1'
    #)
    extracted_text = "" # とりあえずテキストファイルの中身を空にした対応 TODO
    # テンプレートマッチングで画像内検出
    if find_template_in_image(resource_path("resources/tag_img/zenei.png"), processed_img):
        extracted_text += "前衛タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/jyusou.png"), processed_img):
        extracted_text += "重装タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/hojyo.png"), processed_img):
        extracted_text += "補助タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/sogeki.png"), processed_img):
        extracted_text += "狙撃タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/senpou.png"), processed_img):
        extracted_text += "先鋒タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/iryo.png"), processed_img):
        extracted_text += "医療タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/jyutushi.png"), processed_img):
        extracted_text += "術師タイプ\n"
    if find_template_in_image(resource_path("resources/tag_img/enkyori.png"), processed_img):
        extracted_text += "遠距離\n"
    if find_template_in_image(resource_path("resources/tag_img/kinkyori.png"), processed_img):
        extracted_text += "近距離\n"
    if find_template_in_image(resource_path("resources/tag_img/cost.png"), processed_img):
        extracted_text += "COST回復\n"
    if find_template_in_image(resource_path("resources/tag_img/bougyo.png"), processed_img):
        extracted_text += "防御\n"
    if find_template_in_image(resource_path("resources/tag_img/shoki.png"), processed_img):
        extracted_text += "初期\n"
    if find_template_in_image(resource_path("resources/tag_img/karyoku.png"), processed_img):
        extracted_text += "火力\n"
    if find_template_in_image(resource_path("resources/tag_img/seizon.png"), processed_img):
        extracted_text += "生存\n"
    if find_template_in_image(resource_path("resources/tag_img/hani.png"), processed_img):
        extracted_text += "範囲攻撃\n"
    if find_template_in_image(resource_path("resources/tag_img/gensoku.png"), processed_img):
        extracted_text += "減速\n"
    if find_template_in_image(resource_path("resources/tag_img/kyousei.png"), processed_img):
        extracted_text += "強制移動\n"
    if find_template_in_image(resource_path("resources/tag_img/kensei.png"), processed_img):
        extracted_text += "牽制\n"
    if find_template_in_image(resource_path("resources/tag_img/shien.png"), processed_img):
        extracted_text += "支援\n"
    if find_template_in_image(resource_path("resources/tag_img/robot.png"), processed_img):
        extracted_text += "ロボット\n"
    if find_template_in_image(resource_path("resources/tag_img/syoukan.png"), processed_img):
        extracted_text += "召喚\n"
    if find_template_in_image(resource_path("resources/tag_img/chiryou.png"), processed_img):
        extracted_text += "治療\n"
    if find_template_in_image(resource_path("resources/tag_img/bakuhatsu.png"), processed_img):
        extracted_text += "爆発力\n"
    if find_template_in_image(resource_path("resources/tag_img/jyakuka.png"), processed_img):
        extracted_text += "弱化\n"

    matched_tags = [tag for tag in tags if tag in extracted_text]
    return matched_tags, extracted_text

# 解析開始処理
def start_analysis():
    try:
        if screenshot is None:
            messagebox.showerror("エラー", "キャプチャされた画像がありません。")
            return
        extracted_tags, extracted_text = analyze_image()
        data = {
            #"タグ": tags,
            #"解析結果": ["取得済み" if tag in extracted_tags else "未取得" for tag in tags]
        }
        df = pd.DataFrame(data)
        save_results(df, extracted_text)
    except Exception as e:
        messagebox.showerror("エラー", str(e))

if __name__ == "__main__":
    capture_window()