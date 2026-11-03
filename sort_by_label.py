"""Раскладывает фотосессию по папкам товаров, читая артикул с фото этикетки.

Съёмка идёт сериями: несколько кадров товара и последним — этикетка
(по умолчанию по 3 кадра). Скрипт распознаёт текст на этикетке (Tesseract OCR),
находит артикул по шаблону и кладёт всю серию в папку с именем артикула. Если
артикул не распознан, папка называется по имени файла этикетки с пометкой
«не распознан_», чтобы такие папки было легко найти и проверить.

Нужен установленный Tesseract OCR: https://github.com/tesseract-ocr/tesseract
(в Windows путь к tesseract.exe можно указать через --tesseract).

Примеры:
    python sort_by_label.py examples/shoot -o result/sorted
    python sort_by_label.py examples/shoot -o result/sorted --pattern "K[A-Z]{3}\\d{3}[A-Z]{2} +[A-Z]{3}"
"""
import argparse
import re
import shutil
from pathlib import Path

import pytesseract

from photo_tools.files import list_images
from photo_tools.ocr import DEFAULT_ARTICLE_PATTERN, find_article, read_text

_FORBIDDEN = re.compile(r'[\\/:*?"<>|]')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="папка с кадрами съёмки")
    parser.add_argument("-o", "--output", default="result/sorted", help="куда разложить папки товаров")
    parser.add_argument("--group-size", type=int, default=3, help="кадров в серии, этикетка — последний (по умолчанию 3)")
    parser.add_argument("--pattern", default=DEFAULT_ARTICLE_PATTERN, help="регулярное выражение артикула")
    parser.add_argument("--lang", default="eng", help="языки Tesseract, например eng или rus+eng")
    parser.add_argument("--move", action="store_true", help="переносить файлы, а не копировать")
    parser.add_argument("--tesseract", help=r"путь к tesseract.exe, например C:\Program Files\Tesseract-OCR\tesseract.exe")
    args = parser.parse_args()

    if args.tesseract:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract

    photos = list_images(args.source)
    size = args.group_size
    if len(photos) % size:
        print(f"Внимание: {len(photos)} кадров не делится на серии по {size}, последняя серия неполная — пропущу её")

    output = Path(args.output)
    recognized = 0
    for start in range(0, len(photos) - size + 1, size):
        series = photos[start:start + size]
        label = series[-1]
        article = find_article(read_text(label, args.lang), args.pattern)
        if article:
            recognized += 1
            folder_name = _FORBIDDEN.sub("_", article)
        else:
            folder_name = f"не распознан_{label.stem}"
        target = output / folder_name
        target.mkdir(parents=True, exist_ok=True)
        for path in series:
            (shutil.move if args.move else shutil.copy2)(str(path), str(target / path.name))
        print(f"{label.name}: {article or 'артикул не найден'} → {target.name}/ ({len(series)} фото)")

    series_count = len(photos) // size
    print(f"Серий: {series_count}, артикул распознан: {recognized}, не распознан: {series_count - recognized}")


if __name__ == "__main__":
    main()
