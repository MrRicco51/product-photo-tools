"""Поиск фотографий и безопасные операции с файлами."""
import re
import uuid
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def natural_key(path):
    """Сортировка «как в проводнике»: 2.jpg раньше 10.jpg, DSC_9 раньше DSC_10."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", Path(path).name)]


def list_images(folder):
    """Фотографии в папке (без подпапок) в естественном порядке."""
    folder = Path(folder)
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
                  key=natural_key)


def list_subfolders(folder):
    """Подпапки (обычно одна папка = один товар) в естественном порядке."""
    return sorted((p for p in Path(folder).iterdir() if p.is_dir()), key=natural_key)


def rename_in_order(files, names):
    """Переименовывает files[i] → names[i] в той же папке, ничего не затирая.

    Простое переименование по очереди опасно: если в папке уже есть «2.jpg»,
    а первым идёт «a.jpg» → «1.jpg», «b.jpg» → «2.jpg», то существующий «2.jpg»
    будет перезаписан или удалён. Поэтому сначала все файлы получают временные
    уникальные имена, а потом — итоговые.
    """
    temporary = []
    for path in files:
        tmp = path.with_name(f".tmp_{uuid.uuid4().hex}{path.suffix}")
        path.rename(tmp)
        temporary.append(tmp)
    result = []
    for tmp, name in zip(temporary, names):
        target = tmp.with_name(name)
        tmp.rename(target)
        result.append(target)
    return result
