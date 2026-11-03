"""Находит папки товаров, где первым фото стоит этикетка, а не сам товар.

На маркетплейсе первое фото — обложка карточки, и этикетка на этом месте
выглядит как брак. Скрипт проверяет первое фото каждой папки, сохраняет отчёт
CSV и по флагу --fix переносит этикетку в конец (префикс «zzz_» в имени).

Примеры:
    python find_label_photos.py examples/catalog
    python find_label_photos.py examples/catalog --fix
"""
import argparse
import csv
from pathlib import Path

from photo_tools.files import list_images, list_subfolders
from photo_tools.labels import analyze

REPORT_FIELDS = ["папка", "файл", "is_label", "confidence", "rule", "white_ratio", "lines_ratio", "aspect_ratio", "contrast"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", help="папка, внутри которой папки товаров")
    parser.add_argument("--limit", type=int, help="проверить только первые N папок")
    parser.add_argument("--report", default="result/label_report.csv", help="куда сохранить отчёт")
    parser.add_argument("--fix", action="store_true", help="перенести найденные этикетки в конец папки")
    args = parser.parse_args()

    folders = list_subfolders(args.root)[:args.limit]
    rows, found = [], []
    for folder in folders:
        photos = list_images(folder)
        if not photos:
            continue
        first = photos[0]
        try:
            score = analyze(first)
        except ValueError as error:
            print(f"  {error}")
            continue
        rows.append({"папка": folder.name, "файл": first.name, **{k: (round(v, 4) if isinstance(v, float) else v)
                                                                   for k, v in score.as_dict().items()}})
        if score.is_label:
            found.append((folder, first, photos))
            print(f"ЭТИКЕТКА  {folder.name}/{first.name}  ({score.rule}, белого {score.white_ratio:.0%})")

    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig — чтобы Excel открыл кириллицу
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Проверено папок: {len(rows)}, этикеток на первом месте: {len(found)}. Отчёт: {report}")

    if args.fix:
        fixed = 0
        for folder, first, photos in found:
            if len(photos) > 1:
                first.rename(folder / f"zzz_{first.name}")
                fixed += 1
        print(f"Перенесено в конец: {fixed}")


if __name__ == "__main__":
    main()
