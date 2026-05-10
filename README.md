# Convertisseur UI PY

Application desktop PySide6 pour convertir des fichiers Qt Designer `.ui` en modules Python `.py`.

## Fonctionnalites

- Conversion simple d'un fichier `.ui` vers un fichier `.py`
- Conversion batch d'un dossier complet de fichiers `.ui`
- Option pour inclure ou non un footer de preview VS Code
- Validation preventive des chemins et noms de sortie
- Interface graphique avec logs, apercu du chemin final et actions post-conversion

## Structure du projet

- `main.py`: point d'entree GUI
- `logic/convert_ui_to_py.py`: logique de conversion CLI et batch
- `logic/main_window.py`: logique de fenetre principale
- `logic/validation.py`: validations pre-conversion
- `interface/convertisseur.ui`: source Qt Designer
- `interface/convertisseur.py`: UI generee
- `tests/`: suite de tests (unitaires + GUI)

## Prerequis

- Python 3.11+
- `pyside6-uic` disponible (installe via `PySide6`)

## Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Lancer l'application

```bash
source .venv/bin/activate
python main.py
```

## Utilisation CLI

### Conversion simple

```bash
python logic/convert_ui_to_py.py interface/convertisseur.ui --output interface/convertisseur.py --overwrite
```

### Conversion batch

```bash
python logic/convert_ui_to_py.py --input-dir interface --output-dir interface --recursive --overwrite
```

### Sans footer VS Code

```bash
python logic/convert_ui_to_py.py interface/convertisseur.ui --no-preview-footer --overwrite
```

## Qualite et tests

```bash
source .venv/bin/activate
pytest -q
```

Test d'integration reel (plus lent):

```bash
pytest -q -m slow
```

## CI GitHub Actions

Le workflow CI execute automatiquement:

- verification de synchro `convertisseur.ui -> convertisseur.py`
- tests pytest

## Contribution

Les contributions sont bienvenues. Ouvrez une issue ou une pull request en decrivant clairement:

- le probleme observe
- les etapes de reproduction
- le resultat attendu

## Licence

Ce projet est distribue sous licence MIT. Voir `LICENSE`.
