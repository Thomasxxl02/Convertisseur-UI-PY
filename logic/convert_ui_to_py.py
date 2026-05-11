#!/usr/bin/env python3
"""Convertit un fichier Qt Designer .ui en module Python avec PySide6."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import sysconfig
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_UI_FILE = Path("interface/convertisseur.ui")
DEFAULT_GENERATED_FILE = Path("interface/convertisseur.py")


@dataclass
class ConversionOutcome:
    success: bool
    exit_code: int
    user_message: str
    technical_details: str | None = None


@dataclass
class BatchConversionOutcome:
    success_count: int
    failure_count: int
    outcomes: list[tuple[Path, Path, ConversionOutcome]]


def build_parser() -> argparse.ArgumentParser:
    # Définit l'interface en ligne de commande du script.
    parser = argparse.ArgumentParser(
        description="Convertit un fichier .ui en module Python avec PySide6."
    )
    parser.add_argument(
        "ui_file",
        nargs="?",
        type=Path,
        help="Chemin du fichier .ui à convertir.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Dossier contenant des fichiers .ui à convertir en lot.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Inclut les sous-dossiers lors de la conversion avec --input-dir.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Chemin du fichier .py de sortie. Si omis, le nom du .ui est repris avec l'extension .py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Dossier de sortie utilisé quand --output n'est pas fourni.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Autorise l'écrasement du fichier de sortie s'il existe déjà.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Délai max (secondes) pour pyside6-uic avant annulation.",
    )
    parser.add_argument(
        "--sync-default-ui",
        action="store_true",
        help=(
            "Régénère automatiquement interface/convertisseur.py depuis "
            "interface/convertisseur.ui."
        ),
    )
    parser.add_argument(
        "--no-preview-footer",
        action="store_true",
        help="N'ajoute pas le footer de prévisualisation VS Code dans les fichiers générés.",
    )
    return parser


def resolve_output_path(ui_file: Path, output: Path | None, output_dir: Path | None) -> Path:
    # Si un chemin explicite est fourni, il est prioritaire.
    if output is not None:
        return output

    # Sinon, on génère automatiquement le nom de sortie à partir du .ui.
    target_dir = output_dir if output_dir is not None else ui_file.parent
    return target_dir / f"{ui_file.stem}.py"


def _resolve_uic_command() -> list[str]:
    # Recherche d'abord dans le PATH puis dans l'environnement Python actif.
    executable_from_path = shutil.which("pyside6-uic")
    if executable_from_path:
        return [executable_from_path]

    script_dir = Path(sysconfig.get_path("scripts") or "")
    candidates = (
        script_dir / "pyside6-uic",
        script_dir / "pyside6-uic.exe",
        script_dir / "pyside6-uic.bat",
        Path(sys.executable).with_name("pyside6-uic"),
        Path(sys.executable).with_name("pyside6-uic.exe"),
        Path(sys.executable).with_name("pyside6-uic.bat"),
    )
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate)]

    raise FileNotFoundError(
        "La commande pyside6-uic est introuvable. Installe PySide6 ou active l'environnement virtuel."
    )


def _read_ui_metadata(ui_file: Path) -> tuple[str, str]:
    # Lit les métadonnées minimales nécessaires pour générer un point d'entrée d'aperçu.
    try:
        root = ET.fromstring(ui_file.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        raise ValueError(f"Impossible de lire le fichier .ui: {ui_file}") from exc

    ui_class_name = root.findtext("./class")
    widget = root.find("./widget")
    widget_class = widget.get("class") if widget is not None else None

    if not ui_class_name or not widget_class:
        raise ValueError(f"Le fichier .ui est incomplet ou invalide: {ui_file}")

    return ui_class_name, widget_class


def _build_vscode_preview_footer(ui_class_name: str, widget_class: str) -> str:
    # Rend le module généré lançable directement avec le bouton Run/Debug de VS Code.
    return (
        "\n\n"
        "# VS Code preview entry point for the generated UI module.\n"
        "from PySide6 import QtWidgets as _QtWidgets\n\n"
        "def _create_preview_widget():\n"
        f"    widget_class = getattr(_QtWidgets, \"{widget_class}\", None)\n"
        "    if widget_class is None:\n"
        f"        raise RuntimeError(\"Classe Qt introuvable pour l'aperçu: {widget_class}\")\n"
        "\n"
        "    widget = widget_class()\n"
        f"    ui = Ui_{ui_class_name}()\n"
        "    ui.setupUi(widget)\n"
        "    return widget\n\n"
        "def main() -> int:\n"
        "    import sys\n\n"
        "    app = _QtWidgets.QApplication.instance()\n"
        "    owns_app = app is None\n"
        "    if app is None:\n"
        "        app = _QtWidgets.QApplication(sys.argv)\n\n"
        "    preview_widget = _create_preview_widget()\n"
        "    preview_widget.show()\n\n"
        "    if owns_app:\n"
        "        return app.exec()\n"
        "    return 0\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )


def _append_vscode_preview_footer(ui_file: Path, output_file: Path) -> None:
    # Ajoute un point d'entrée stable après génération pour l'usage direct dans VS Code.
    if not output_file.exists():
        raise FileNotFoundError(f"Le fichier généré est introuvable: {output_file}")

    ui_class_name, widget_class = _read_ui_metadata(ui_file)
    content = output_file.read_text(encoding="utf-8")
    content += _build_vscode_preview_footer(ui_class_name, widget_class)
    output_file.write_text(content, encoding="utf-8")


def run_uic(
    ui_file: Path,
    output_file: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    *,
    append_preview_footer: bool = True,
) -> None:
    if timeout_seconds <= 0:
        raise ValueError("Le timeout doit être strictement positif.")

    # Recherche l'exécutable pyside6-uic (PATH + environnement Python actif).
    uic_command = _resolve_uic_command()

    # Crée le dossier de destination si nécessaire.
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Lance la conversion .ui -> .py et échoue explicitement si la commande retourne une erreur.
    subprocess.run(
        [*uic_command, str(ui_file), "-o", str(output_file)],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if append_preview_footer:
        _append_vscode_preview_footer(ui_file, output_file)


def execute_conversion(
    ui_file: Path,
    output_file: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    *,
    append_preview_footer: bool = True,
) -> ConversionOutcome:
    # Encapsule la conversion dans un résultat structuré exploitable par CLI et GUI.
    try:
        run_uic(
            ui_file,
            output_file,
            timeout_seconds=timeout_seconds,
            append_preview_footer=append_preview_footer,
        )
    except subprocess.TimeoutExpired as exc:
        details = f"Commande: {exc.cmd} | timeout: {exc.timeout}s"
        return ConversionOutcome(
            success=False,
            exit_code=124,
            user_message="Conversion annulée (timeout).",
            technical_details=details,
        )
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        details = (
            f"Commande: {exc.cmd} | code retour: {exc.returncode} | "
            f"stderr: {stderr_text or '<vide>'}"
        )
        return ConversionOutcome(
            success=False,
            exit_code=exc.returncode,
            user_message="Échec de conversion via pyside6-uic.",
            technical_details=details,
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        return ConversionOutcome(
            success=False,
            exit_code=1,
            user_message="Erreur système pendant la conversion.",
            technical_details=repr(exc),
        )

    return ConversionOutcome(
        success=True,
        exit_code=0,
        user_message=f"Conversion réussie: {ui_file} -> {output_file}",
    )


def sync_default_ui_module(timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> Path:
    # Point d'entrée dédié pour maintenir le fichier généré aligné avec la source .ui.
    if not DEFAULT_UI_FILE.exists():
        raise ValueError(f"Fichier source .ui introuvable: {DEFAULT_UI_FILE}")

    run_uic(DEFAULT_UI_FILE, DEFAULT_GENERATED_FILE, timeout_seconds=timeout_seconds)
    return DEFAULT_GENERATED_FILE


def _collect_ui_files(input_dir: Path, recursive: bool) -> list[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Le dossier d'entrée est invalide: {input_dir}")

    iterator = input_dir.rglob("*.ui") if recursive else input_dir.glob("*.ui")
    return sorted(path for path in iterator if path.is_file())


def execute_batch_conversion(
    input_dir: Path,
    output_dir: Path | None,
    overwrite: bool,
    timeout_seconds: float,
    recursive: bool,
    *,
    append_preview_footer: bool = True,
) -> BatchConversionOutcome:
    ui_files = _collect_ui_files(input_dir, recursive)
    if not ui_files:
        raise ValueError(f"Aucun fichier .ui trouvé dans: {input_dir}")

    outcomes: list[tuple[Path, Path, ConversionOutcome]] = []
    success_count = 0
    failure_count = 0

    for ui_file in ui_files:
        if output_dir is None:
            target_output = resolve_output_path(ui_file, output=None, output_dir=None)
        else:
            relative_parent = ui_file.parent.relative_to(input_dir)
            target_output = output_dir / relative_parent / f"{ui_file.stem}.py"

        if target_output.exists() and not overwrite:
            outcome = ConversionOutcome(
                success=False,
                exit_code=2,
                user_message=f"Le fichier de sortie existe déjà: {target_output}",
                technical_details="Utilise --overwrite pour autoriser l'écrasement en mode batch.",
            )
        else:
            outcome = execute_conversion(
                ui_file,
                target_output,
                timeout_seconds=timeout_seconds,
                append_preview_footer=append_preview_footer,
            )

        outcomes.append((ui_file, target_output, outcome))
        if outcome.success:
            success_count += 1
        else:
            failure_count += 1

    return BatchConversionOutcome(
        success_count=success_count,
        failure_count=failure_count,
        outcomes=outcomes,
    )


def main() -> int:
    # Analyse des arguments utilisateur.
    parser = build_parser()
    args = parser.parse_args()

    timeout_seconds: float = args.timeout
    append_preview_footer = not args.no_preview_footer
    if timeout_seconds <= 0:
        parser.error("--timeout doit être strictement positif.")

    if args.ui_file is not None and args.input_dir is not None:
        parser.error("Utilise soit ui_file, soit --input-dir, mais pas les deux.")

    if args.sync_default_ui:
        outcome = execute_conversion(
            DEFAULT_UI_FILE,
            DEFAULT_GENERATED_FILE,
            timeout_seconds=timeout_seconds,
            append_preview_footer=append_preview_footer,
        )
        if not outcome.success:
            print(
                "Erreur pendant la synchronisation UI par défaut: "
                f"{outcome.user_message}",
                file=sys.stderr,
            )
            if outcome.technical_details:
                print(f"Détail technique: {outcome.technical_details}", file=sys.stderr)
            return outcome.exit_code

        print(f"Synchronisation réussie: {DEFAULT_UI_FILE} -> {DEFAULT_GENERATED_FILE}")
        return 0

    if args.input_dir is not None:
        try:
            batch_outcome = execute_batch_conversion(
                input_dir=args.input_dir,
                output_dir=args.output_dir,
                overwrite=args.overwrite,
                timeout_seconds=timeout_seconds,
                recursive=args.recursive,
                append_preview_footer=append_preview_footer,
            )
        except ValueError as exc:
            parser.error(str(exc))

        for ui_file, output_file, outcome in batch_outcome.outcomes:
            prefix = "OK" if outcome.success else "KO"
            print(f"[{prefix}] {ui_file} -> {output_file}: {outcome.user_message}")
            if outcome.technical_details and not outcome.success:
                print(f"    Détail technique: {outcome.technical_details}", file=sys.stderr)

        print(
            f"Batch terminé: {batch_outcome.success_count} succès, "
            f"{batch_outcome.failure_count} échec(s)."
        )
        return 0 if batch_outcome.failure_count == 0 else 1

    if args.ui_file is None:
        parser.error("Le paramètre ui_file est requis (ou utilise --input-dir/--sync-default-ui).")

    # Validation basique du fichier source.
    ui_file: Path = args.ui_file
    if not ui_file.exists():
        parser.error(f"Le fichier source n'existe pas: {ui_file}")
    if ui_file.suffix.lower() != ".ui":
        parser.error("Le fichier source doit avoir l'extension .ui")

    # Résolution du chemin de sortie selon les options passées.
    output_file = resolve_output_path(ui_file, args.output, args.output_dir)

    # Protège contre l'écrasement involontaire, sauf si --overwrite est demandé.
    if output_file.exists() and not args.overwrite:
        parser.error(
            f"Le fichier de sortie existe déjà: {output_file}. Utilise --overwrite pour l'écraser."
        )

    outcome = execute_conversion(
        ui_file,
        output_file,
        timeout_seconds=timeout_seconds,
        append_preview_footer=append_preview_footer,
    )
    if not outcome.success:
        print(outcome.user_message, file=sys.stderr)
        if outcome.technical_details:
            print(f"Détail technique: {outcome.technical_details}", file=sys.stderr)
        return outcome.exit_code

    # Message de succès standard.
    print(outcome.user_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
