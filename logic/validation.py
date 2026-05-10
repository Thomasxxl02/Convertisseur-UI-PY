from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    # Indique si toutes les validations sont passées.
    is_valid: bool
    # Liste des erreurs collectées pendant la validation.
    errors: list[str]


def validate_before_conversion(ui_path: Path, output_path: Path) -> ValidationResult:
    # Point d'entrée principal: agrège toutes les validations nécessaires.
    errors: list[str] = []

    # Vérifie la lecture et la cohérence XML du fichier .ui.
    ui_content = _read_ui_content(ui_path, errors)
    if ui_content:
        root = _parse_ui_xml(ui_content, errors)
        if root is not None:
            errors.extend(_validate_ui_structure(root))
            errors.extend(_validate_custom_widgets(root))

    # Vérifie les droits d'écriture et la validité du chemin de sortie.
    errors.extend(_validate_output_permissions(output_path))

    return ValidationResult(is_valid=not errors, errors=errors)


def _read_ui_content(ui_path: Path, errors: list[str]) -> str:
    # Lit le contenu texte du .ui en UTF-8.
    try:
        content = ui_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Impossible de lire le fichier .ui: {exc}")
        return ""

    # Rejette explicitement les fichiers vides.
    if not content.strip():
        errors.append("Le fichier .ui est vide.")
    return content


def _parse_ui_xml(content: str, errors: list[str]) -> ET.Element | None:
    # Parse le XML et remonte une erreur lisible en cas d'échec.
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        errors.append(f"Le fichier .ui contient un XML invalide: {exc}")
        return None


def _validate_ui_structure(root: ET.Element) -> list[str]:
    # Contrôle la structure minimale attendue d'un .ui Qt Designer.
    errors: list[str] = []

    if root.tag != "ui":
        errors.append("La racine XML doit être la balise <ui>.")

    if root.find("widget") is None:
        errors.append("Le fichier .ui ne contient aucun widget racine.")

    if root.find("class") is None:
        errors.append("Le fichier .ui ne contient pas de classe principale (<class>).")

    return errors


def _validate_custom_widgets(root: ET.Element) -> list[str]:
    # Vérifie la cohérence entre widgets custom déclarés et réellement utilisés.
    errors: list[str] = []

    declared_custom_classes: set[str] = set()
    for custom_widget in root.findall("./customwidgets/customwidget"):
        class_name = (custom_widget.findtext("class") or "").strip()
        header_name = (custom_widget.findtext("header") or "").strip()

        # Une déclaration de custom widget sans nom de classe est invalide.
        if not class_name:
            errors.append("Un <customwidget> est déclaré sans balise <class>.")
            continue

        declared_custom_classes.add(class_name)
        # Sans header, l'import Python généré peut être incomplet.
        if not header_name:
            errors.append(
                f"Le widget custom '{class_name}' est déclaré sans <header>, import non résolu possible."
            )

    # Recense toutes les classes de widgets présentes dans l'arbre XML.
    used_widget_classes = {
        element.attrib.get("class", "").strip()
        for element in root.findall(".//widget")
        if element.attrib.get("class", "").strip()
    }

    # Les classes non Qt (non préfixées par Q) doivent être déclarées en customwidgets.
    unresolved_custom = [
        class_name
        for class_name in sorted(used_widget_classes)
        if not class_name.startswith("Q") and class_name not in declared_custom_classes
    ]
    if unresolved_custom:
        errors.append(
            "Widgets custom non résolus: " + ", ".join(unresolved_custom)
        )

    return errors


def _validate_output_permissions(output_path: Path) -> list[str]:
    # Vérifie si le fichier cible est modifiable et si le dossier de sortie est accessible.
    errors: list[str] = []
    output_dir = output_path.parent

    # Si le fichier existe déjà, il doit être inscriptible.
    if output_path.exists() and not os.access(output_path, os.W_OK):
        errors.append(f"Le fichier de sortie n'est pas modifiable: {output_path}")
        return errors

    # Si le chemin parent existe, il doit être un dossier.
    if output_dir.exists() and not output_dir.is_dir():
        errors.append(f"Le chemin de sortie n'est pas un dossier: {output_dir}")
        return errors

    # Remonte jusqu'au premier parent existant pour tester les permissions réelles.
    probe = output_dir
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent

    if not probe.exists():
        errors.append(f"Impossible de valider le dossier de sortie: {output_dir}")
        return errors

    # La création de fichiers exige écriture + traversée de dossier.
    if not os.access(probe, os.W_OK | os.X_OK):
        errors.append(
            f"Droits insuffisants pour créer/écrire dans le dossier de sortie: {output_dir}"
        )

    return errors
