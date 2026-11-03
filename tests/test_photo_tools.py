import shutil

import numpy as np
import pytest
from PIL import Image

from photo_tools.files import list_images, natural_key, rename_in_order
from photo_tools.labels import score_image
from photo_tools.ocr import find_article
from photo_tools.resize import resize_image, target_size


def test_natural_sort(tmp_path):
    for name in ["10.jpg", "2.jpg", "1.jpg", "notes.txt"]:
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in list_images(tmp_path)] == ["1.jpg", "2.jpg", "10.jpg"]
    assert natural_key("DSC_9.jpg") < natural_key("DSC_10.jpg")


def test_rename_in_order_does_not_overwrite_existing_names(tmp_path):
    # «2.jpg» уже есть и стоит в списке третьим: наивное переименование «b.jpg» → «2.jpg» затёрло бы его
    contents = {"a.jpg": b"A", "b.jpg": b"B", "2.jpg": b"OLD2"}
    for name, data in contents.items():
        (tmp_path / name).write_bytes(data)
    files = [tmp_path / "a.jpg", tmp_path / "b.jpg", tmp_path / "2.jpg"]
    rename_in_order(files, ["1.jpg", "2.jpg", "3.jpg"])
    assert (tmp_path / "1.jpg").read_bytes() == b"A"
    assert (tmp_path / "2.jpg").read_bytes() == b"B"
    assert (tmp_path / "3.jpg").read_bytes() == b"OLD2"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["1.jpg", "2.jpg", "3.jpg"]


@pytest.mark.parametrize("image_size, expected", [
    ((900, 1350), (2048, 2684)),   # вертикальное
    ((1500, 1000), (2684, 2048)),  # горизонтальное
])
def test_target_size_follows_orientation(image_size, expected):
    assert target_size(image_size, (2048, 2684)) == expected
    assert target_size(image_size, (2684, 2048)) == expected


@pytest.mark.parametrize("mode", ["pad", "crop", "stretch"])
def test_resize_exact_size(mode):
    img = Image.new("RGB", (900, 1350), "red")
    assert resize_image(img, (720, 540), mode).size == (540, 720)


def test_pad_keeps_proportions_with_white_fields():
    img = Image.new("RGB", (1000, 1000), "red")        # квадрат в вертикальный кадр
    result = resize_image(img, (300, 400), "pad")
    assert result.getpixel((150, 5)) == (255, 255, 255)  # поле сверху
    assert result.getpixel((150, 200)) == (255, 0, 0)    # сам кадр


def test_label_detection():
    white = np.full((1200, 900), 250, dtype=np.uint8)
    white[300:340, 80:800] = 0                            # «строка текста»
    product = np.random.default_rng(0).integers(60, 180, (1200, 900), dtype=np.uint8)
    assert score_image(white).is_label
    assert not score_image(product).is_label


@pytest.mark.parametrize("text, expected", [
    ("Артикул\nklrl421mn  blk 105\nрост 170", "KLRL421MN BLK 105"),   # регистр и двойной пробел
    ("KNWD118PB WHT", "KNWD118PB WHT"),                               # размер необязателен
    ("100% COTTON", None),
])
def test_find_article(text, expected):
    assert find_article(text) == expected


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract не установлен")
def test_ocr_on_example_label():
    from pathlib import Path
    from photo_tools.ocr import read_text
    label = Path(__file__).parent.parent / "examples" / "shoot" / "IMG_0003.jpg"
    assert find_article(read_text(label)) == "KLRL421MN BLK 105"
