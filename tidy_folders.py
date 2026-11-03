"""Наводит порядок в папках товаров: оставляет первые N фото и нумерует их 1, 2, 3…

Одна подпапка = один товар (например, «NW-1024»). Лишние фото по умолчанию не
удаляются, а переносятся в подпапку «_лишние», чтобы ошибку можно было исправить.

Примеры:
    python tidy_folders.py examples/catalog --keep 5 --dry-run    # только показать, что будет сделано
    python tidy_folders.py examples/catalog --keep 5 --rename
    python tidy_folders.py examples/catalog --keep-only 2 4 6    # оставить 2-е, 4-е и 6-е фото
"""
import argparse
import shutil

from photo_tools.files import list_images, list_subfolders, rename_in_order

EXTRA_FOLDER = "_лишние"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", help="папка, внутри которой папки товаров")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--keep", type=int, help="оставить первые N фото")
    selection.add_argument("--keep-only", type=int, nargs="+", metavar="N",
                           help="оставить фото с этими номерами по порядку (с 1)")
    parser.add_argument("--rename", action="store_true", help="переименовать оставшиеся в 1, 2, 3…")
    parser.add_argument("--delete", action="store_true", help=f"удалять лишние, а не переносить в «{EXTRA_FOLDER}»")
    parser.add_argument("--dry-run", action="store_true", help="ничего не менять, только показать план")
    args = parser.parse_args()

    totals = {"папок": 0, "оставлено": 0, "убрано": 0, "переименовано": 0}
    for folder in list_subfolders(args.root):
        photos = list_images(folder)
        if not photos:
            continue
        if args.keep:
            keep = photos[:args.keep]
        elif args.keep_only:
            keep = [photos[n - 1] for n in sorted(set(args.keep_only)) if 0 < n <= len(photos)]
        else:
            keep = photos
        extra = [p for p in photos if p not in keep]
        new_names = [f"{i}{p.suffix.lower()}" for i, p in enumerate(keep, start=1)] if args.rename else None

        totals["папок"] += 1
        totals["оставлено"] += len(keep)
        totals["убрано"] += len(extra)
        renamed = sum(1 for p, n in zip(keep, new_names or []) if p.name != n)
        totals["переименовано"] += renamed
        print(f"{folder.name}: фото {len(photos)} → оставить {len(keep)}, убрать {len(extra)}"
              + (f", переименовать {renamed}" if args.rename else ""))
        if args.dry_run:
            continue

        for path in extra:
            if args.delete:
                path.unlink()
            else:
                (folder / EXTRA_FOLDER).mkdir(exist_ok=True)
                shutil.move(str(path), str(folder / EXTRA_FOLDER / path.name))
        if args.rename and renamed:
            rename_in_order(keep, new_names)

    print("Итого: " + ", ".join(f"{k} {v}" for k, v in totals.items()) + (" (пробный запуск, файлы не изменены)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
