from __future__ import annotations

from pathlib import Path

from logic.validation import (
    suggest_output_filename,
    validate_before_conversion,
    validate_output_filename_crossplatform,
)


def _write_ui(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_validate_before_conversion_accepts_minimal_valid_ui(tmp_path: Path) -> None:
    ui_file = tmp_path / "valid.ui"
    output_file = tmp_path / "generated" / "valid.py"

    _write_ui(
        ui_file,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
    )

    result = validate_before_conversion(ui_file, output_file)

    assert result.is_valid is True
    assert result.errors == []


def test_validate_before_conversion_rejects_invalid_xml(tmp_path: Path) -> None:
    ui_file = tmp_path / "invalid.ui"
    output_file = tmp_path / "invalid.py"

    _write_ui(
        ui_file,
        """<ui>
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\">  
</ui>
""",
    )

    result = validate_before_conversion(ui_file, output_file)

    assert result.is_valid is False
    assert any("XML invalide" in error for error in result.errors)


def test_validate_before_conversion_detects_unresolved_custom_widget(tmp_path: Path) -> None:
    ui_file = tmp_path / "custom_missing.ui"
    output_file = tmp_path / "custom_missing.py"

    _write_ui(
        ui_file,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\">
    <widget class=\"FancyChart\" name=\"fancyChart\"/>
  </widget>
</ui>
""",
    )

    result = validate_before_conversion(ui_file, output_file)

    assert result.is_valid is False
    assert any("Widgets custom non résolus" in error for error in result.errors)


def test_validate_before_conversion_reports_atomic_write_probe_failure(
    tmp_path: Path, monkeypatch
) -> None:
    ui_file = tmp_path / "valid.ui"
    output_file = tmp_path / "generated" / "valid.py"

    _write_ui(
        ui_file,
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
    )

    monkeypatch.setattr(
        "logic.validation._probe_directory_write_atomic",
        lambda _directory: "probe refusé",
    )

    result = validate_before_conversion(ui_file, output_file)

    assert result.is_valid is False
    assert any("probe refusé" in error for error in result.errors)


# Tests pour la validation cross-plateforme du nom de sortie
def test_validate_output_filename_crossplatform_accepts_valid_names() -> None:
    valid_names = [
        "converter.py",
        "my_widget.py",
        "Main_Window_UI.py",
        "file_2025.py",
        "simple.py",
    ]
    
    for name in valid_names:
        errors = validate_output_filename_crossplatform(name)
        assert errors == [], f"'{name}' devrait être valide mais a des erreurs: {errors}"


def test_validate_output_filename_crossplatform_rejects_windows_reserved_names() -> None:
    # Noms réservés Windows (case-insensitive)
    reserved_names = [
        "CON.py",
        "PRN.py",
        "NUL.py",
        "AUX.py",
        "COM1.py",
        "COM9.py",
        "LPT1.py",
        "LPT9.py",
        "con.py",
        "prn.py",
        "aux.py",
        "lpt1.py",
    ]
    
    for name in reserved_names:
        errors = validate_output_filename_crossplatform(name)
        assert errors, f"'{name}' devrait être rejeté comme nom réservé Windows"
        assert any("nom réservé Windows" in error for error in errors)


def test_validate_output_filename_crossplatform_rejects_path_separators() -> None:
    invalid_names = [
        "path/to/file.py",
        "path\\to\\file.py",
        "folder/output.py",
    ]
    
    for name in invalid_names:
        errors = validate_output_filename_crossplatform(name)
        assert errors, f"'{name}' contient des séparateurs et devrait être rejeté"
        assert any("séparateur de chemin" in error for error in errors)


def test_validate_output_filename_crossplatform_rejects_invalid_characters() -> None:
    invalid_names = [
        "file:name.py",
        "file*name.py",
        'file"name.py',
        "file<name.py",
        "file>name.py",
        "file|name.py",
        "file?name.py",
    ]
    
    for name in invalid_names:
        errors = validate_output_filename_crossplatform(name)
        assert errors, f"'{name}' contient des caractères invalides et devrait être rejeté"
        assert any("caractères invalides" in error for error in errors)


def test_validate_output_filename_crossplatform_normalizes_trailing_spaces() -> None:
    name_with_spaces = "myfile.py  "
    errors = validate_output_filename_crossplatform(name_with_spaces)
    
    assert errors, "Les espaces trailing devraient être détectés"
    assert any("trailing" in error.lower() for error in errors)


def test_validate_output_filename_crossplatform_rejects_trailing_dot() -> None:
    errors = validate_output_filename_crossplatform("myfile.py.")

    assert errors, "Le point trailing devrait être détecté"
    assert any("trailing" in error.lower() for error in errors)


def test_validate_output_filename_crossplatform_accepts_multiple_dots() -> None:
    valid_names = [
        "file.backup.py",
        "my.module.py",
        "a.b.c.py",
    ]

    for name in valid_names:
        errors = validate_output_filename_crossplatform(name)
        assert errors == [], f"'{name}' devrait être accepté mais a des erreurs: {errors}"


def test_suggest_output_filename_cleans_trailing_and_invalid_chars() -> None:
    suggested, messages = suggest_output_filename(" bad:name.py. ")

    assert suggested == " bad_name.py"
    assert messages


def test_suggest_output_filename_handles_empty_after_cleanup() -> None:
    suggested, messages = suggest_output_filename("...")

    assert suggested == "sortie"
    assert any("Nom vide" in message for message in messages)


def test_suggest_output_filename_renames_windows_reserved_name() -> None:
    suggested, messages = suggest_output_filename("CON")

    assert suggested == "CON_fichier"
    assert any("Windows" in message for message in messages)


