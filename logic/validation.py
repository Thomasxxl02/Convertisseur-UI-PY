from __future__ import annotations

import os
import re
import tempfile
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

    errors.extend(_validate_ui_file(ui_path))
    errors.extend(_validate_output_target(output_path))

    return ValidationResult(is_valid=not errors, errors=errors)


def _validate_ui_file(ui_path: Path) -> list[str]:
    # Regroupe les validations liées au contenu/format du fichier .ui.
    errors: list[str] = []
    ui_content = _read_ui_content(ui_path, errors)
    if not ui_content:
        return errors

    root = _parse_ui_xml(ui_content, errors)
    if root is None:
        return errors

    errors.extend(_validate_ui_structure(root))
    errors.extend(_validate_custom_widgets(root))
    return errors


def _validate_output_target(output_path: Path) -> list[str]:
    # Regroupe les validations liées au chemin de sortie et aux permissions.
    return _validate_output_permissions(output_path)


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


def validate_output_filename_crossplatform(filename: str) -> list[str]:
    """
    Valide le nom de fichier de sortie pour la cross-plateforme.
    
    Vérifie:
    - Noms réservés Windows (CON, PRN, NUL, COM1-9, LPT1-9, AUX)
    - Caractères invalides (/, \\, :, *, ?, ", <, >, |, \\x00-\\x1f)
    - Espaces/points trailing (interdits)
    - Unicité du nom après normalisation
    
    Returns:
        Liste des erreurs trouvées (vide si valide).
    """
    errors: list[str] = []
    
    original_filename = filename
    filename = filename.rstrip(" .")
    
    # Détecte les espaces/points trailing et les rejette explicitement.
    if original_filename != filename:
        errors.append(
            "Le nom de sortie ne doit pas contenir d'espaces/points trailing. "
            f"Valeur reçue: '{original_filename}'"
        )

    if not filename:
        errors.append("Le nom de sortie est vide après normalisation.")
        return errors
    
    # Vérifie les séparateurs de chemin
    if any(sep in filename for sep in ("/", "\\")):
        errors.append("Le nom de sortie ne doit pas contenir de séparateur de chemin (/ ou \\).")
    
    # Vérifie les caractères invalides sur tous les OS
    invalid_chars = r'[:*?"<>|]'
    if re.search(invalid_chars, filename):
        invalid_found = "".join(set(re.findall(invalid_chars, filename)))
        errors.append(
            f"Le nom de sortie contient des caractères invalides: {invalid_found}"
        )
    
    # Vérifie les caractères de contrôle (\\x00-\\x1f)
    if any(ord(c) < 0x20 for c in filename):
        errors.append("Le nom de sortie contient des caractères de contrôle invalides.")
    
    # Noms réservés Windows (sans extension, case-insensitive)
    windows_reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    
    # Extrait le nom de base (avant l'extension)
    name_base = filename.rsplit(".", 1)[0] if "." in filename else filename
    if name_base.upper() in windows_reserved:
        errors.append(
            f"'{filename}' utilise un nom réservé Windows. "
            f"Noms interdits: {', '.join(sorted(windows_reserved))}"
        )
    
    return errors


def suggest_output_filename(filename: str) -> tuple[str, list[str]]:
    """Propose un nom de sortie nettoyé sans bloquer l'utilisateur."""
    messages: list[str] = []
    original = filename

    candidate = filename.rstrip(" .")
    if candidate != filename:
        messages.append("Suppression automatique des espaces/points en fin de nom.")

    candidate = candidate.replace("/", "_").replace("\\", "_")

    invalid_chars = r'[:*?"<>|]'
    replaced_invalid = re.sub(invalid_chars, "_", candidate)
    if replaced_invalid != candidate:
        messages.append("Remplacement automatique des caractères non autorisés.")
    candidate = replaced_invalid

    if any(ord(char) < 0x20 for char in candidate):
        candidate = "".join("_" if ord(char) < 0x20 else char for char in candidate)
        messages.append("Suppression automatique des caractères de contrôle.")

    if not candidate:
        candidate = "sortie"
        messages.append("Nom vide remplacé par 'sortie'.")

    windows_reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    name_base = candidate.rsplit(".", 1)[0] if "." in candidate else candidate
    if name_base.upper() in windows_reserved:
        candidate = f"{candidate}_fichier"
        messages.append("Nom réservé Windows renommé automatiquement.")

    return candidate, messages


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

    # Validation complémentaire: création + écriture + renommage atomique + suppression.
    atomic_probe_error = _probe_directory_write_atomic(probe)
    if atomic_probe_error:
        errors.append(
            f"Droits insuffisants pour écrire dans le dossier de sortie ({probe}): {atomic_probe_error}"
        )

    return errors


def _probe_directory_write_atomic(directory: Path) -> str | None:
    temp_path: Path | None = None
    renamed_path: Path | None = None

    try:
        fd, raw_path = tempfile.mkstemp(prefix=".convertisseur_write_probe_", dir=str(directory))
        temp_path = Path(raw_path)

        with os.fdopen(fd, "wb") as temp_file:
            temp_file.write(b"ok")
            temp_file.flush()
            os.fsync(temp_file.fileno())

        renamed_path = temp_path.with_suffix(temp_path.suffix + ".done")
        os.replace(temp_path, renamed_path)
        renamed_path.unlink()
        return None
    except OSError as exc:
        return str(exc)
    finally:
        for candidate in (temp_path, renamed_path):
            if candidate is None:
                continue
            try:
                if candidate.exists():
                    candidate.unlink()
            except OSError:
                # Best effort cleanup: l'erreur originale reste prioritaire.
                pass
