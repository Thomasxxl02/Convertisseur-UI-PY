from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from logic.convert_ui_to_py import BatchConversionOutcome, ConversionOutcome
from logic.main_window import ConverterMainWindow
from logic.validation import ValidationResult


def test_gui_convert_main_flow_success(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    captured: dict[str, Path] = {}

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )

    def fake_execute_conversion(
        source: Path,
        destination: Path,
        timeout_seconds: float = 30.0,
        *,
        append_preview_footer: bool = True,
    ) -> ConversionOutcome:
        captured["source"] = source
        captured["destination"] = destination
        return ConversionOutcome(
            success=True,
            exit_code=0,
            user_message=f"Conversion réussie: {source} -> {destination}",
        )

    monkeypatch.setattr("logic.main_window.execute_conversion", fake_execute_conversion)
    monkeypatch.setattr(
        "logic.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)

    window.ui.uiFileLineEdit.setText(str(ui_file))
    window.ui.outputDirLineEdit.setText(str(output_dir))
    window.ui.outputNameLineEdit.setText("generated_module")

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: "source" in captured and "destination" in captured, timeout=2000)

    assert captured["source"] == ui_file
    assert captured["destination"] == output_dir / "generated_module.py"
    assert "Conversion réussie" in window.ui.logTextEdit.toPlainText()


def test_gui_live_validation_disables_convert_until_valid(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)

    assert window.ui.convertButton.isEnabled() is False
    assert "Sélectionnez un fichier .ui source." in window.ui.validationMessageLabel.text()

    window.ui.uiFileLineEdit.setText(str(ui_file))

    assert window.ui.convertButton.isEnabled() is True
    assert window.ui.validationMessageLabel.text() == ""
    assert "Sortie finale:" in window.outputPathPreviewLabel.text()


def test_gui_convert_does_not_show_popup_for_validation_errors(qtbot, monkeypatch) -> None:
    popup_calls: list[str] = []

    monkeypatch.setattr(
        "logic.main_window.QMessageBox.critical",
        lambda *_args, **_kwargs: popup_calls.append("critical"),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)

    assert window.ui.convertButton.isEnabled() is False
    window._convert()  # noqa: SLF001

    assert popup_calls == []
    assert "Sélectionnez un fichier .ui source." in window.ui.validationMessageLabel.text()


def test_gui_convert_overwrite_refused_does_not_call_run_uic(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    ui_file = tmp_path / "input.ui"
    output_dir = tmp_path / "out"
    output_file = output_dir / "generated.py"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )
    output_dir.mkdir(parents=True)
    output_file.write_text("ancien", encoding="utf-8")

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )

    calls: list[str] = []

    def fake_execute_conversion(
        _source: Path,
        _destination: Path,
        timeout_seconds: float = 30.0,
        *,
        append_preview_footer: bool = True,
    ) -> ConversionOutcome:
        calls.append("called")
        return ConversionOutcome(success=True, exit_code=0, user_message="ok")

    monkeypatch.setattr("logic.main_window.execute_conversion", fake_execute_conversion)
    monkeypatch.setattr(
        "logic.main_window.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)

    window.ui.uiFileLineEdit.setText(str(ui_file))
    window.ui.outputDirLineEdit.setText(str(output_dir))
    window.ui.outputNameLineEdit.setText("generated")

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)

    assert calls == []
    assert "Conversion annulée (écrasement refusé)." in window.ui.logTextEdit.toPlainText()


def test_gui_convert_handles_called_process_error(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )
    monkeypatch.setattr(
        "logic.main_window.execute_conversion",
        lambda *_args, **_kwargs: ConversionOutcome(
            success=False,
            exit_code=2,
            user_message="Échec de conversion via pyside6-uic.",
            technical_details="stderr: boom",
        ),
    )

    popup_messages: list[str] = []
    monkeypatch.setattr(
        "logic.main_window.QMessageBox.critical",
        lambda _parent, _title, message: popup_messages.append(message),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)
    window.ui.uiFileLineEdit.setText(str(ui_file))
    window.ui.outputDirLineEdit.setText(str(tmp_path / "out"))
    window.ui.outputNameLineEdit.setText("generated")

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: bool(popup_messages), timeout=2000)

    assert popup_messages
    assert "Échec de conversion via pyside6-uic" in popup_messages[0]


def test_gui_convert_handles_os_error(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )
    monkeypatch.setattr(
        "logic.main_window.execute_conversion",
        lambda *_args, **_kwargs: ConversionOutcome(
            success=False,
            exit_code=1,
            user_message="Erreur système pendant la conversion: permission refusée",
            technical_details="OSError('permission refusée')",
        ),
    )

    popup_messages: list[str] = []
    monkeypatch.setattr(
        "logic.main_window.QMessageBox.critical",
        lambda _parent, _title, message: popup_messages.append(message),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)
    window.ui.uiFileLineEdit.setText(str(ui_file))
    window.ui.outputDirLineEdit.setText(str(tmp_path / "out"))
    window.ui.outputNameLineEdit.setText("generated")

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: bool(popup_messages), timeout=2000)

    assert popup_messages
    assert "Erreur système pendant la conversion" in popup_messages[0]


def test_gui_convert_handles_timeout_error(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(is_valid=True, errors=[]),
    )
    monkeypatch.setattr(
        "logic.main_window.execute_conversion",
        lambda *_args, **_kwargs: ConversionOutcome(
            success=False,
            exit_code=124,
            user_message="Conversion annulée (timeout).",
            technical_details="Commande: ['pyside6-uic'] | timeout: 30.0s",
        ),
    )

    popup_messages: list[str] = []
    monkeypatch.setattr(
        "logic.main_window.QMessageBox.critical",
        lambda _parent, _title, message: popup_messages.append(message),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)
    window.ui.uiFileLineEdit.setText(str(ui_file))
    window.ui.outputDirLineEdit.setText(str(tmp_path / "out"))
    window.ui.outputNameLineEdit.setText("generated")

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: bool(popup_messages), timeout=2000)

    assert popup_messages
    assert "Conversion annulée (timeout)" in popup_messages[0]


def test_gui_close_does_not_ask_confirmation_when_disabled(qtbot, monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        ConverterMainWindow,
        "_ask_close_confirmation",
        lambda self: calls.append("asked") or QMessageBox.StandardButton.No,
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)
    window.show()

    window.close()

    assert calls == []


def test_gui_close_asks_confirmation_when_enabled(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(
        ConverterMainWindow,
        "_ask_close_confirmation",
        lambda self: QMessageBox.StandardButton.No,
    )

    window = ConverterMainWindow(confirm_on_close=True, use_settings=False)
    qtbot.addWidget(window)
    window.show()

    window.close()

    assert window.isVisible() is True


def test_gui_validation_guidance_is_non_blocking(qtbot, tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.validate_before_conversion",
        lambda _ui, _out: ValidationResult(
            is_valid=False,
            errors=["Widgets custom non résolus: FancyChart"],
        ),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)

    window.ui.uiFileLineEdit.setText(str(ui_file))

    assert window.ui.convertButton.isEnabled() is True
    assert "Conseil:" in window.ui.validationMessageLabel.text()


def test_gui_batch_convert_flow_success(qtbot, tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    input_dir.mkdir()
    output_dir.mkdir()

    ui_a = input_dir / "a.ui"
    ui_b = input_dir / "b.ui"
    ui_a.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\"><class>MainWindow</class><widget class=\"QMainWindow\" name=\"MainWindow\"/></ui>
""",
        encoding="utf-8",
    )
    ui_b.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\"><class>MainWindow</class><widget class=\"QMainWindow\" name=\"MainWindow\"/></ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "logic.main_window.execute_batch_conversion",
        lambda **_kwargs: BatchConversionOutcome(
            success_count=2,
            failure_count=0,
            outcomes=[
                (
                    ui_a,
                    output_dir / "a.py",
                    ConversionOutcome(success=True, exit_code=0, user_message="ok a"),
                ),
                (
                    ui_b,
                    output_dir / "b.py",
                    ConversionOutcome(success=True, exit_code=0, user_message="ok b"),
                ),
            ],
        ),
    )

    window = ConverterMainWindow(confirm_on_close=False, use_settings=False)
    qtbot.addWidget(window)
    window.batchModeCheckBox.setChecked(True)
    window.ui.uiFileLineEdit.setText(str(input_dir))
    window.ui.outputDirLineEdit.setText(str(output_dir))

    qtbot.mouseClick(window.ui.convertButton, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: "Batch terminé: 2 succès, 0 échec(s)." in window.ui.logTextEdit.toPlainText(),
        timeout=2000,
    )

    assert "ok a" in window.ui.logTextEdit.toPlainText()
    assert "ok b" in window.ui.logTextEdit.toPlainText()
