from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from logic import convert_ui_to_py
from logic.convert_ui_to_py import resolve_output_path


def test_resolve_output_path_prioritizes_explicit_output(tmp_path: Path) -> None:
    ui_file = tmp_path / "screen.ui"
    explicit_output = tmp_path / "custom" / "module.py"

    result = resolve_output_path(ui_file, output=explicit_output, output_dir=None)

    assert result == explicit_output


def test_resolve_output_path_uses_output_dir_when_no_explicit_output(tmp_path: Path) -> None:
    ui_file = tmp_path / "dialog.ui"
    output_dir = tmp_path / "generated"

    result = resolve_output_path(ui_file, output=None, output_dir=output_dir)

    assert result == output_dir / "dialog.py"


def test_resolve_output_path_falls_back_to_ui_parent(tmp_path: Path) -> None:
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    ui_file = ui_dir / "window.ui"

    result = resolve_output_path(ui_file, output=None, output_dir=None)

    assert result == ui_dir / "window.py"


def _write_valid_ui(path: Path) -> None:
    path.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>MainWindow</class>
  <widget class=\"QMainWindow\" name=\"MainWindow\"/>
</ui>
""",
        encoding="utf-8",
    )


def test_main_returns_124_on_timeout(tmp_path: Path, monkeypatch, capsys) -> None:
    ui_file = tmp_path / "input.ui"
    _write_valid_ui(ui_file)

    monkeypatch.setattr(sys, "argv", ["convert", str(ui_file)])

    def fake_run_uic(
        _ui: Path,
        _out: Path,
        timeout_seconds: float = 30.0,
        *,
        append_preview_footer: bool = True,
    ) -> None:
        raise subprocess.TimeoutExpired(cmd=["pyside6-uic"], timeout=timeout_seconds)

    monkeypatch.setattr(convert_ui_to_py, "run_uic", fake_run_uic)

    exit_code = convert_ui_to_py.main()
    captured = capsys.readouterr()

    assert exit_code == 124
    assert "Conversion annulée (timeout)" in captured.err


def test_main_returns_subprocess_return_code_on_called_process_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    ui_file = tmp_path / "input.ui"
    _write_valid_ui(ui_file)

    monkeypatch.setattr(sys, "argv", ["convert", str(ui_file)])

    def fake_run_uic(
        _ui: Path,
        _out: Path,
        timeout_seconds: float = 30.0,
        *,
        append_preview_footer: bool = True,
    ) -> None:
        raise subprocess.CalledProcessError(
            returncode=7,
            cmd=["pyside6-uic"],
            stderr="échec simulé",
        )

    monkeypatch.setattr(convert_ui_to_py, "run_uic", fake_run_uic)

    exit_code = convert_ui_to_py.main()
    captured = capsys.readouterr()

    assert exit_code == 7
    assert "Échec de conversion via pyside6-uic." in captured.err
    assert "code retour: 7" in captured.err
    assert "échec simulé" in captured.err


def test_main_returns_1_on_os_error(tmp_path: Path, monkeypatch, capsys) -> None:
    ui_file = tmp_path / "input.ui"
    _write_valid_ui(ui_file)

    monkeypatch.setattr(sys, "argv", ["convert", str(ui_file)])
    monkeypatch.setattr(
        convert_ui_to_py,
        "run_uic",
        lambda _ui, _out, timeout_seconds=30.0, append_preview_footer=True: (
            _ for _ in ()
        ).throw(OSError("permission refusée")),
    )

    exit_code = convert_ui_to_py.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "permission refusée" in captured.err


def test_run_uic_uses_scripts_directory_fallback_when_path_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    ui_file = tmp_path / "input.ui"
    output_file = tmp_path / "generated.py"
    _write_valid_ui(ui_file)
    script_dir = tmp_path / "venv_scripts"
    script_dir.mkdir()
    fallback_uic = script_dir / "pyside6-uic"
    fallback_uic.write_text("", encoding="utf-8")

    monkeypatch.setattr(convert_ui_to_py.shutil, "which", lambda _name: None)
    monkeypatch.setattr(convert_ui_to_py.sysconfig, "get_path", lambda _name: str(script_dir))

    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        output_file.write_text(
            "class Ui_Input(object):\n    def setupUi(self, Input):\n        pass\n",
            encoding="utf-8",
        )
        return None

    monkeypatch.setattr(convert_ui_to_py.subprocess, "run", fake_run)

    convert_ui_to_py.run_uic(ui_file, output_file)

    assert commands
    assert commands[0][0] == str(fallback_uic)


def test_run_uic_appends_vscode_preview_footer(tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "dialog.ui"
    output_file = tmp_path / "dialog.py"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>Dialog</class>
  <widget class=\"QDialog\" name=\"Dialog\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(convert_ui_to_py, "_resolve_uic_command", lambda: ["pyside6-uic"])

    def fake_run(command, **kwargs):
        output_file.write_text(
            "class Ui_Dialog(object):\n    def setupUi(self, Dialog):\n        pass\n",
            encoding="utf-8",
        )
        return None

    monkeypatch.setattr(convert_ui_to_py.subprocess, "run", fake_run)

    convert_ui_to_py.run_uic(ui_file, output_file)

    generated_content = output_file.read_text(encoding="utf-8")
    assert "# VS Code preview entry point for the generated UI module." in generated_content
    assert 'widget_class = getattr(_QtWidgets, "QDialog", None)' in generated_content
    assert "app = _QtWidgets.QApplication.instance()" in generated_content
    assert "app = _QtWidgets.QApplication(sys.argv)" in generated_content
    assert "ui = Ui_Dialog()" in generated_content
    assert 'if __name__ == "__main__":' in generated_content


def test_main_refuses_existing_output_without_overwrite(tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "input.ui"
    output_file = tmp_path / "out.py"
    _write_valid_ui(ui_file)
    output_file.write_text("ancien", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["convert", str(ui_file), "--output", str(output_file)])

    with pytest.raises(SystemExit) as exc_info:
        convert_ui_to_py.main()

    assert exc_info.value.code == 2


def test_run_uic_can_skip_vscode_preview_footer(tmp_path: Path, monkeypatch) -> None:
    ui_file = tmp_path / "dialog.ui"
    output_file = tmp_path / "dialog.py"
    ui_file.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ui version=\"4.0\">
  <class>Dialog</class>
  <widget class=\"QDialog\" name=\"Dialog\"/>
</ui>
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(convert_ui_to_py, "_resolve_uic_command", lambda: ["pyside6-uic"])

    def fake_run(command, **kwargs):
        output_file.write_text(
            "class Ui_Dialog(object):\n    def setupUi(self, Dialog):\n        pass\n",
            encoding="utf-8",
        )
        return None

    monkeypatch.setattr(convert_ui_to_py.subprocess, "run", fake_run)

    convert_ui_to_py.run_uic(ui_file, output_file, append_preview_footer=False)

    generated_content = output_file.read_text(encoding="utf-8")
    assert "# VS Code preview entry point for the generated UI module." not in generated_content


def test_execute_batch_conversion_reports_mixed_results(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    ui_ok = input_dir / "ok.ui"
    ui_fail = input_dir / "fail.ui"
    _write_valid_ui(ui_ok)
    _write_valid_ui(ui_fail)

    output_dir = tmp_path / "outputs"

    def fake_execute_conversion(
        ui_file: Path,
        output_file: Path,
        timeout_seconds: float = 30.0,
        *,
        append_preview_footer: bool = True,
    ) -> convert_ui_to_py.ConversionOutcome:
        if ui_file.name == "fail.ui":
            return convert_ui_to_py.ConversionOutcome(
                success=False,
                exit_code=7,
                user_message="échec simulé",
                technical_details="boom",
            )
        return convert_ui_to_py.ConversionOutcome(
            success=True,
            exit_code=0,
            user_message="ok",
        )

    monkeypatch.setattr(convert_ui_to_py, "execute_conversion", fake_execute_conversion)

    batch_outcome = convert_ui_to_py.execute_batch_conversion(
        input_dir=input_dir,
        output_dir=output_dir,
        overwrite=True,
        timeout_seconds=30.0,
        recursive=False,
    )

    assert batch_outcome.success_count == 1
    assert batch_outcome.failure_count == 1
    assert len(batch_outcome.outcomes) == 2


def test_main_batch_mode_returns_1_on_partial_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    _write_valid_ui(input_dir / "a.ui")

    monkeypatch.setattr(sys, "argv", ["convert", "--input-dir", str(input_dir)])
    monkeypatch.setattr(
        convert_ui_to_py,
        "execute_batch_conversion",
        lambda **kwargs: convert_ui_to_py.BatchConversionOutcome(
            success_count=0,
            failure_count=1,
            outcomes=[
                (
                    input_dir / "a.ui",
                    input_dir / "a.py",
                    convert_ui_to_py.ConversionOutcome(
                        success=False,
                        exit_code=7,
                        user_message="échec",
                        technical_details="detail",
                    ),
                )
            ],
        ),
    )

    exit_code = convert_ui_to_py.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Batch terminé" in captured.out


@pytest.mark.slow
def test_run_uic_real_integration(tmp_path: Path) -> None:
    if convert_ui_to_py.shutil.which("pyside6-uic") is None:
        pytest.skip("pyside6-uic indisponible dans l'environnement de test")

    ui_file = tmp_path / "real.ui"
    output_file = tmp_path / "real.py"
    _write_valid_ui(ui_file)

    convert_ui_to_py.run_uic(ui_file, output_file, timeout_seconds=30.0)

    generated_content = output_file.read_text(encoding="utf-8")
    assert "class Ui_MainWindow" in generated_content
    assert "# VS Code preview entry point for the generated UI module." in generated_content
