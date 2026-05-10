# Contributing

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Development flow

1. Creer une branche depuis `main`
2. Faire des commits atomiques
3. Lancer les tests localement
4. Ouvrir une Pull Request

## Local checks

```bash
source .venv/bin/activate
bash scripts/check_ui_generated_sync.sh
pytest -q
```

## Notes for UI files

- Toute modification de `interface/convertisseur.ui` doit etre suivie d'une regeneration de `interface/convertisseur.py`.
- Le script `scripts/check_ui_generated_sync.sh` verifie cette regle.
