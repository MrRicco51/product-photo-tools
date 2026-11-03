"""Распознавание фото этикетки (а не самого товара) по признакам изображения.

Этикетка на фото — это в основном белый фон и строки текста. Товар на
съёмке — цветной, с плавными переходами. Признаки считаются на уменьшенной
копии кадра, поэтому анализ тысячи фотографий занимает минуты, а не часы.
"""
from dataclasses import asdict, dataclass

import cv2
import numpy as np

ANALYSIS_WIDTH = 800       # ширина копии для анализа, px
WHITE_LEVEL = 210          # яркость, с которой пиксель считается «белым»


@dataclass
class LabelScore:
    is_label: bool
    confidence: float
    white_ratio: float     # доля почти белых пикселей
    lines_ratio: float     # доля пикселей на горизонтальных линиях (строки текста)
    aspect_ratio: float    # отношение длинной стороны к короткой
    contrast: float        # стандартное отклонение яркости
    rule: str              # какое правило сработало

    def as_dict(self):
        return asdict(self)


def read_gray(path):
    """Читает изображение в оттенках серого. cv2.imread не открывает пути с кириллицей
    в Windows, поэтому файл читается байтами и декодируется отдельно."""
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"не удалось прочитать изображение: {path}")
    return img


def score_image(gray):
    """Считает признаки и применяет правила (от самого уверенного к менее уверенному)."""
    h, w = gray.shape[:2]
    if w > ANALYSIS_WIDTH:
        gray = cv2.resize(gray, (ANALYSIS_WIDTH, int(h * ANALYSIS_WIDTH / w)), interpolation=cv2.INTER_AREA)
        h, w = gray.shape[:2]
    pixels = h * w

    white_ratio = float(np.count_nonzero(gray > WHITE_LEVEL) / pixels)
    edges = cv2.Canny(gray, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)
    lines_ratio = float(np.count_nonzero(horizontal) / pixels)
    aspect_ratio = max(w / h, h / w)
    contrast = float(np.std(gray))

    rules = [
        (white_ratio > 0.75, 0.9, "почти весь кадр белый"),
        (white_ratio > 0.6 and lines_ratio > 0.008, 0.8, "белый фон и строки текста"),
        (aspect_ratio > 2.2 and white_ratio > 0.5, 0.7, "узкий кадр на белом фоне"),
        (contrast < 35 and white_ratio > 0.6, 0.6, "низкий контраст на белом фоне"),
    ]
    for matched, confidence, rule in rules:
        if matched:
            return LabelScore(True, confidence, white_ratio, lines_ratio, aspect_ratio, contrast, rule)
    return LabelScore(False, 0.0, white_ratio, lines_ratio, aspect_ratio, contrast, "")


def analyze(path):
    return score_image(read_gray(path))
