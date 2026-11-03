"""Приводит все фото в папке (и подпапках) к размеру площадки.

Горизонтальные кадры получают «перевёрнутый» размер: 2048×2684 → 2684×2048.
По умолчанию исходники не трогаются — результат пишется в отдельную папку
с той же структурой подпапок.

Примеры:
    python resize_photos.py examples/photos -o result/resized --size 2048x2684
    python resize_photos.py examples/photos -o result/small --size 720x540 --mode crop
"""
import argparse
from pathlib import Path

from PIL import Image

from photo_tools.files import IMAGE_EXTENSIONS, natural_key
from photo_tools.resize import MODES, resize_image


def parse_size(text):
    try:
        width, height = (int(x) for x in text.lower().replace("×", "x").split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("размер в формате 2048x2684")
    return width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="папка с фотографиями (обрабатывается вместе с подпапками)")
    parser.add_argument("-o", "--output", help="куда сохранить (по умолчанию result/resized)")
    parser.add_argument("--size", type=parse_size, default=(2048, 2684), help="размер, по умолчанию 2048x2684")
    parser.add_argument("--mode", choices=MODES, default="pad",
                        help="pad — поля, crop — обрезка, stretch — растянуть (по умолчанию pad)")
    parser.add_argument("--quality", type=int, default=92, help="качество JPEG, 1–95")
    parser.add_argument("--in-place", action="store_true", help="перезаписать исходные файлы (осторожно!)")
    args = parser.parse_args()

    source = Path(args.source)
    output = source if args.in_place else Path(args.output or "result/resized")
    files = sorted((p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
                   key=lambda p: [natural_key(part) for part in p.relative_to(source).parts])
    print(f"Фото: {len(files)}, размер {args.size[0]}×{args.size[1]}, режим «{args.mode}»")

    done = errors = 0
    for path in files:
        target = output / path.relative_to(source)
        try:
            with Image.open(path) as img:
                result = resize_image(img, args.size, args.mode)
            target.parent.mkdir(parents=True, exist_ok=True)
            options = {"quality": args.quality, "optimize": True} if target.suffix.lower() in (".jpg", ".jpeg") else {}
            result.save(target, **options)
            done += 1
        except Exception as error:
            errors += 1
            print(f"  ошибка: {path} — {error}")
    print(f"Готово: {done}, ошибок: {errors}. Результат: {output}")


if __name__ == "__main__":
    main()
