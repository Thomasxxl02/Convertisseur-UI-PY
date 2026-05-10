from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def _read_ui_window_title(ui_path: Path) -> str:
    root = ET.fromstring(ui_path.read_text(encoding="utf-8"))
    title = root.findtext("./widget/property[@name='windowTitle']/string")
    if title is None:
        raise AssertionError("windowTitle introuvable dans le fichier .ui")
    return title


def _read_generated_window_title(generated_py_path: Path) -> str:
    content = generated_py_path.read_text(encoding="utf-8")
    match = re.search(
        r'setWindowTitle\(QCoreApplication\.translate\("MainWindow",\s*u"(?P<title>(?:\\.|[^"\\])*)",\s*None\)\)',
        content,
    )
    if match is None:
        raise AssertionError("setWindowTitle introuvable dans le fichier Python généré")

    escaped_title = match.group("title")
    return bytes(escaped_title, "utf-8").decode("unicode_escape")


def test_generated_window_title_matches_ui_source() -> None:
    ui_title = _read_ui_window_title(Path("interface/convertisseur.ui"))
    generated_title = _read_generated_window_title(Path("interface/convertisseur.py"))

    assert generated_title == ui_title
