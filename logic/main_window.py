from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from interface.convertisseur import Ui_MainWindow
from logic.convert_ui_to_py import resolve_output_path, run_uic
from logic.validation import validate_before_conversion


class ConverterMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # Initialise l'interface générée depuis Qt Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_quit_action()
        self._connect_signals()
        self.statusBar().showMessage("Prêt")

    def _setup_quit_action(self) -> None:
        # Ajoute une action "Quitter" avec le raccourci standard de la plateforme.
        self.quit_action = QAction("Quitter", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.ui.menuQuitter.addAction(self.quit_action)

    def _connect_signals(self) -> None:
        # Connecte les interactions UI aux méthodes métier.
        self.ui.browseUiButton.clicked.connect(self._browse_ui_file)
        self.ui.browseOutputDirButton.clicked.connect(self._browse_output_dir)
        self.ui.convertButton.clicked.connect(self._convert)
        self.ui.actionApropos.triggered.connect(self._show_about)
        self.quit_action.triggered.connect(self.close)

    def _browse_ui_file(self) -> None:
        # Ouvre un sélecteur pour choisir le fichier .ui source.
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier .ui",
            str(Path.cwd()),
            "Qt Designer (*.ui)",
        )
        if not selected_file:
            return

        ui_path = Path(selected_file)
        self.ui.uiFileLineEdit.setText(str(ui_path))

        # Préremplit les champs de sortie s'ils sont vides.
        if not self.ui.outputDirLineEdit.text().strip():
            self.ui.outputDirLineEdit.setText(str(ui_path.parent))
        if not self.ui.outputNameLineEdit.text().strip():
            self.ui.outputNameLineEdit.setText(ui_path.stem)

        self._log(f"UI sélectionnée: {ui_path}")

    def _browse_output_dir(self) -> None:
        # Ouvre un sélecteur de dossier pour la destination du fichier .py.
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de sortie",
            self.ui.outputDirLineEdit.text().strip() or str(Path.cwd()),
        )
        if not selected_dir:
            return

        output_dir = Path(selected_dir)
        self.ui.outputDirLineEdit.setText(str(output_dir))
        self._log(f"Dossier de sortie: {output_dir}")

    def _build_output_path(self, ui_path: Path) -> Path:
        # Construit le chemin final de sortie à partir des champs UI.
        output_dir_text = self.ui.outputDirLineEdit.text().strip()
        output_name_text = self.ui.outputNameLineEdit.text().strip()

        output_dir = Path(output_dir_text) if output_dir_text else None
        if output_name_text:
            output_name = output_name_text
            # Garantit l'extension .py si l'utilisateur ne l'a pas saisie.
            if not output_name.lower().endswith(".py"):
                output_name = f"{output_name}.py"
            base_dir = output_dir if output_dir is not None else ui_path.parent
            return base_dir / output_name

        # Fallback: même logique que le convertisseur CLI.
        return resolve_output_path(ui_path, output=None, output_dir=output_dir)

    def _convert(self) -> None:
        # Valide les entrées utilisateur minimales avant de lancer la conversion.
        ui_path_text = self.ui.uiFileLineEdit.text().strip()
        if not ui_path_text:
            self._show_error("Le chemin du fichier .ui est requis.")
            return

        ui_path = Path(ui_path_text)
        if not ui_path.exists():
            self._show_error(f"Fichier introuvable: {ui_path}")
            return
        if ui_path.suffix.lower() != ".ui":
            self._show_error("Le fichier source doit avoir l'extension .ui")
            return

        output_path = self._build_output_path(ui_path)

        # Exécute les règles de validation centralisées.
        validation_result = validate_before_conversion(ui_path, output_path)
        if not validation_result.is_valid:
            formatted_errors = "\n".join(f"- {error}" for error in validation_result.errors)
            self._show_error(f"Validation pré-conversion échouée:\n{formatted_errors}")
            return

        # Demande confirmation si le fichier cible existe déjà.
        if output_path.exists():
            answer = QMessageBox.question(
                self,
                "Confirmer l'écrasement",
                f"Le fichier existe déjà:\n{output_path}\n\nVoulez-vous l'écraser ?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._log("Conversion annulée (écrasement refusé).")
                return

        try:
            # Appelle pyside6-uic via la fonction utilitaire.
            run_uic(ui_path, output_path)
        except FileNotFoundError as exc:
            self._show_error(str(exc))
            return
        except Exception as exc:
            self._show_error(f"Erreur de conversion: {exc}")
            return

        self._log(f"Conversion réussie: {ui_path} -> {output_path}")
        self.statusBar().showMessage("Conversion terminée", 5000)

    def _show_about(self) -> None:
        # Affiche une boîte d'information simple sur l'application.
        QMessageBox.information(
            self,
            "À propos",
            "Convertisseur UI → Python\nGénère des modules .py à partir de fichiers .ui (PySide6).",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Intercepte la fermeture pour demander une confirmation utilisateur.
        answer = QMessageBox.question(
            self,
            "Quitter",
            "Voulez-vous vraiment quitter l'application ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            event.accept()
            return

        event.ignore()

    def _show_error(self, message: str) -> None:
        # Centralise l'affichage des erreurs (journal + barre d'état + popup).
        self._log(f"Erreur: {message}")
        self.statusBar().showMessage("Erreur", 5000)
        QMessageBox.critical(self, "Erreur", message)

    def _log(self, message: str) -> None:
        # Ajoute un message dans la zone de log de l'interface.
        self.ui.logTextEdit.append(message)
