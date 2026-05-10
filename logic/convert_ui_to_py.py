#!/usr/bin/env python3
"""Convertit un fichier Qt Designer .ui en module Python avec PySide6."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    # Définit l'interface en ligne de commande du script.
    parser = argparse.ArgumentParser(
        description="Convertit un fichier .ui en module Python avec PySide6."
    )
    parser.add_argument(
        "ui_file",
        type=Path,
        help="Chemin du fichier .ui à convertir.",
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
    return parser


def resolve_output_path(ui_file: Path, output: Path | None, output_dir: Path | None) -> Path:
    # Si un chemin explicite est fourni, il est prioritaire.
    if output is not None:
        return output

    # Sinon, on génère automatiquement le nom de sortie à partir du .ui.
    target_dir = output_dir if output_dir is not None else ui_file.parent
    return target_dir / f"{ui_file.stem}.py"


def run_uic(ui_file: Path, output_file: Path) -> None:
    # Recherche l'exécutable pyside6-uic dans l'environnement courant.
    uic_executable = shutil.which("pyside6-uic")
    if uic_executable is None:
        raise FileNotFoundError(
            "La commande pyside6-uic est introuvable. Installe PySide6 ou active l'environnement virtuel."
        )

    # Crée le dossier de destination si nécessaire.
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Lance la conversion .ui -> .py et échoue explicitement si la commande retourne une erreur.
    subprocess.run(
        [uic_executable, str(ui_file), "-o", str(output_file)],
        check=True,
    )


def main() -> int:
    # Analyse des arguments utilisateur.
    parser = build_parser()
    args = parser.parse_args()

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

    try:
        # Tente la conversion via pyside6-uic.
        run_uic(ui_file, output_file)
    except subprocess.CalledProcessError as exc:
        # Erreur de la commande externe : on relaie le code retour.
        print(f"Erreur lors de la conversion: {exc}", file=sys.stderr)
        return exc.returncode
    except FileNotFoundError as exc:
        # Exécutable introuvable : message clair pour l'utilisateur.
        print(str(exc), file=sys.stderr)
        return 1

    # Message de succès standard.
    print(f"Conversion réussie: {ui_file} -> {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
