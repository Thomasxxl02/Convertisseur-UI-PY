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

## Page de don Stripe Checkout

Une page de don web est disponible dans `page_don.html`.

### Installation des dependances dediees

```bash
source .venv/bin/activate
pip install -r requirements-don.txt
```

### Variables d'environnement

Definis au minimum:

```bash
export STRIPE_SECRET_KEY="sk_test_xxx"
```

Configuration produit/taxe par defaut deja integree:

- STRIPE_PRODUCT_ID=prod_UUeI06vtxJmMsz
- STRIPE_PRODUCT_TAX_CODE=txcd_10000000

Tu peux les surcharger avec des variables d'environnement si besoin.

Tu peux t'aider de `/.env.donation.example` pour les autres options.

### Lancement local

```bash
source .venv/bin/activate
python donate_server.py
```

Puis ouvre `http://localhost:8787`.

## Packaging Linux

Scripts prets a l'emploi:

- `scripts/build_linux_binary.sh`: build PyInstaller Linux (onedir)
- `scripts/build_deb.sh`: build paquet Debian `.deb`

### Generer le binaire Linux

```bash
scripts/build_linux_binary.sh
```

Sortie attendue: `dist/ConvertisseurUiPy/ConvertisseurUiPy`

### Generer le paquet Debian

```bash
scripts/build_deb.sh
```

Sortie attendue: `dist/convertisseur-ui-py_<version>_<arch>.deb`

## Contribution

Les contributions sont bienvenues. Ouvrez une issue ou une pull request en decrivant clairement:

- le probleme observe
- les etapes de reproduction
- le resultat attendu

## Licence

Ce projet est distribue sous licence MIT. Voir `LICENSE`.
