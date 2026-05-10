#!/usr/bin/env python3
"""Lance l'interface Qt du convertisseur UI vers Python."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from logic.main_window import ConverterMainWindow


def main() -> int:
    # Crée l'application Qt en réutilisant les arguments de ligne de commande.
    app = QApplication(sys.argv)
    # Instancie puis affiche la fenêtre principale.
    window = ConverterMainWindow()
    window.show()
    # Démarre la boucle d'événements Qt et renvoie son code de sortie.
    return app.exec()


if __name__ == "__main__":
    # Point d'entrée du script exécuté directement.
    raise SystemExit(main())