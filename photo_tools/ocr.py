"""Распознавание артикула на фото этикетки с помощью Tesseract OCR."""
import re

import cv2
import pytesseract

from .labels import read_gray

# Пример артикула на этикетке: «KLRL421MN BLK 105» — код модели, код цвета, размер
# [ \t]+ — один или несколько пробелов между частями (OCR часто ставит лишние), но не перенос строки
DEFAULT_ARTICLE_PATTERN = r"[A-Z0-9]{6,}[ \t]+[A-Z]{3}(?:[ \t]+\d{3})?"


def prepare_for_ocr(gray):
    """Увеличивает мелкий текст и переводит кадр в чёрно-белый (порог Оцу подбирается сам)."""
    h, w = gray.shape[:2]
    if w < 1500:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def read_text(path, lang="eng"):
    image = prepare_for_ocr(read_gray(path))
    return pytesseract.image_to_string(image, lang=lang, config="--oem 3 --psm 6")


def find_article(text, pattern=DEFAULT_ARTICLE_PATTERN):
    """Первый артикул по шаблону; лишние пробелы схлопываются. Не найден → None."""
    match = re.search(pattern, text.upper())
    return re.sub(r"\s+", " ", match.group(0)).strip() if match else None
