"""Приведение фото к размеру площадки (например, 2048×2684 или 720×540)."""
from PIL import Image, ImageOps

MODES = ("pad", "crop", "stretch")


def target_size(image_size, size):
    """Размер с учётом ориентации: горизонтальное фото получает «перевёрнутый» размер."""
    width, height = image_size
    short, long = sorted(size)
    return (long, short) if width > height else (short, long)


def resize_image(img, size, mode="pad", background=(255, 255, 255)):
    """Возвращает изображение ровно нужного размера.

    pad     — вписать целиком и дополнить полями цвета фона (пропорции сохраняются);
    crop    — заполнить кадр и обрезать лишнее по краям (пропорции сохраняются);
    stretch — растянуть до размера (как в исходной версии скрипта; искажает пропорции).
    """
    img = ImageOps.exif_transpose(img)          # учесть поворот, записанный камерой
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    size = target_size(img.size, size)
    if mode == "stretch":
        return img.resize(size, Image.LANCZOS)
    if mode == "crop":
        return ImageOps.fit(img, size, Image.LANCZOS)
    if mode == "pad":
        return ImageOps.pad(img, size, Image.LANCZOS, color=background)
    raise ValueError(f"Неизвестный режим {mode!r}, допустимы: {MODES}")
