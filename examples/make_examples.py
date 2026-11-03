"""Создаёт синтетические фото для примеров: «товары» — цветные фигуры,
«этикетки» — белый кадр с текстом. Настоящих фотографий в репозитории нет.

    python examples/make_examples.py
"""
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
random.seed(7)


def font(size):
    try:
        return ImageFont.load_default(size=size)       # Pillow ≥ 10.1
    except TypeError:
        return ImageFont.load_default()


def product_photo(size=(900, 1200), color=None):
    """«Товар»: фигура на сером градиентном фоне, как на предметной съёмке."""
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):                                  # вертикальный градиент фона
        shade = 150 + int(60 * y / h)
        draw.line([(0, y), (w, y)], fill=(shade, shade, shade - 10))
    color = color or tuple(random.randint(30, 200) for _ in range(3))
    draw.rounded_rectangle([w * 0.2, h * 0.2, w * 0.8, h * 0.85], radius=60, fill=color)
    draw.ellipse([w * 0.35, h * 0.1, w * 0.65, h * 0.32], fill=tuple(c // 2 for c in color))
    return img.filter(ImageFilter.GaussianBlur(1.5))


def label_photo(lines, size=(900, 1200), readable=True):
    """«Этикетка»: белый кадр со строками текста; readable=False — смазанный кадр."""
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    y = 300
    for i, line in enumerate(lines):
        draw.text((80, y), line, fill="black", font=font(64 if i == 0 else 40))
        y += 110
    if not readable:
        img = img.filter(ImageFilter.GaussianBlur(9))
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=80)


for name in ("catalog", "shoot", "photos"):
    shutil.rmtree(HERE / name, ignore_errors=True)

# 1. Каталог: папка = товар. В двух папках первой лежит этикетка.
catalog = {
    "NW-1024": (6, False), "UF-RP42": (4, True), "PB-77": (7, False), "PB-310": (5, True),
}
for article, (count, label_first) in catalog.items():
    folder = HERE / "catalog" / article
    color = tuple(random.randint(30, 200) for _ in range(3))
    for i in range(1, count + 1):
        img = label_photo([article, "SIZE: M", "MADE IN EXAMPLE"]) if (label_first and i == 1) else product_photo(color=color)
        save(img, folder / f"DSC_{100 + i}.jpg")

# 2. Фотосессия: серии по 3 кадра (товар, товар, этикетка).
series = [("KLRL421MN BLK 105", True), ("KNWD118PB WHT 042", True), ("KUFX907RN GRY 038", False)]
frame = 1
for article, readable in series:
    color = tuple(random.randint(30, 200) for _ in range(3))
    for _ in range(2):
        save(product_photo(color=color), HERE / "shoot" / f"IMG_{frame:04d}.jpg")
        frame += 1
    save(label_photo([article, "COLOR / SIZE", "100% COTTON"], readable=readable), HERE / "shoot" / f"IMG_{frame:04d}.jpg")
    frame += 1

# 3. Фото для изменения размера: вертикальное и горизонтальное.
save(product_photo((900, 1350)), HERE / "photos" / "vertical.jpg")
save(product_photo((1500, 1000)), HERE / "photos" / "sub" / "horizontal.jpg")

print("Примеры созданы в", HERE)
