from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QThread, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
)

from interface.convertisseur import Ui_MainWindow
from logic.convert_ui_to_py import execute_batch_conversion, execute_conversion, resolve_output_path
from logic.validation import (
    suggest_output_filename,
    validate_before_conversion,
    validate_output_filename_crossplatform,
)


LOGGER = logging.getLogger(__name__)
DONATION_PAYMENT_URL = "https://buy.stripe.com/14AaEQ6Cj6PFf6D7v4f3a05"


class ConversionWorker(QObject):
    finished = Signal(object, object)
    failed = Signal(str)

    def __init__(
        self,
        ui_path: Path,
        output_path: Path,
        include_preview_footer: bool,
    ) -> None:
        super().__init__()
        self.ui_path = ui_path
        self.output_path = output_path
        self.include_preview_footer = include_preview_footer

    def run(self) -> None:
        try:
            outcome = execute_conversion(
                self.ui_path,
                self.output_path,
                append_preview_footer=self.include_preview_footer,
            )
        except Exception:  # noqa: BLE001
            LOGGER.exception("Erreur inattendue dans le worker de conversion")
            self.failed.emit("Erreur interne inattendue pendant la conversion.")
            return

        self.finished.emit(self.output_path, outcome)


class BatchConversionWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path | None,
        recursive: bool,
        include_preview_footer: bool,
    ) -> None:
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.recursive = recursive
        self.include_preview_footer = include_preview_footer

    def run(self) -> None:
        try:
            outcome = execute_batch_conversion(
                input_dir=self.input_dir,
                output_dir=self.output_dir,
                overwrite=True,
                timeout_seconds=30.0,
                recursive=self.recursive,
                append_preview_footer=self.include_preview_footer,
            )
        except Exception:  # noqa: BLE001
            LOGGER.exception("Erreur inattendue dans le worker de conversion batch")
            self.failed.emit("Erreur interne inattendue pendant la conversion batch.")
            return

        self.finished.emit(outcome)


class ConverterMainWindow(QMainWindow):
    def __init__(self, *, confirm_on_close: bool = True, use_settings: bool = True) -> None:
        super().__init__()
        self.confirm_on_close = confirm_on_close
        self.use_settings = use_settings
        self._is_converting = False
        self._conversion_thread: QThread | None = None
        self._conversion_worker: QObject | None = None
        self._last_generated_path: Path | None = None
        self._settings = QSettings("ConvertisseurUiPy", "ConvertisseurUiPyApp")
        # Initialise l'interface générée depuis Qt Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_post_conversion_actions()
        self._setup_donation_action()
        self._setup_quit_action()
        if self.use_settings:
            self._load_recent_values()
        self._connect_signals()
        self._update_live_validation()
        self.statusBar().showMessage("Prêt")

    def _setup_post_conversion_actions(self) -> None:
        # Ajoute une zone d'actions optionnelles après succès de conversion.
        self.outputPathPreviewLabel = QLabel("Sortie finale: en attente")
        self.outputPathPreviewLabel.setWordWrap(True)
        self.outputPathPreviewLabel.setToolTip("Le chemin final est recalculé automatiquement.")

        self.previewFooterCheckBox = QCheckBox("Inclure le footer de prévisualisation VS Code")
        self.previewFooterCheckBox.setChecked(True)
        self.batchModeCheckBox = QCheckBox("Mode lot (conversion d'un dossier)")
        self.recursiveBatchCheckBox = QCheckBox("Inclure les sous-dossiers")

        self.openGeneratedFileButton = QPushButton("Ouvrir le fichier généré")
        self.openGeneratedFolderButton = QPushButton("Ouvrir le dossier")
        self.openDonationPageButton = QPushButton("Faire un don")
        self.copyLogsButton = QPushButton("Copier les logs")
        self.clearLogsButton = QPushButton("Effacer les logs")
        self.openGeneratedFileButton.setEnabled(False)
        self.openGeneratedFolderButton.setEnabled(False)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.openGeneratedFileButton)
        actions_layout.addWidget(self.openGeneratedFolderButton)

        logs_layout = QHBoxLayout()
        logs_layout.addWidget(self.openDonationPageButton)
        logs_layout.addWidget(self.copyLogsButton)
        logs_layout.addWidget(self.clearLogsButton)

        log_index = self.ui.verticalLayout_2.indexOf(self.ui.logTextEdit)
        self.ui.verticalLayout_2.insertWidget(log_index, self.outputPathPreviewLabel)
        self.ui.verticalLayout_2.insertWidget(log_index + 1, self.batchModeCheckBox)
        self.ui.verticalLayout_2.insertWidget(log_index + 2, self.recursiveBatchCheckBox)
        self.ui.verticalLayout_2.insertWidget(log_index + 3, self.previewFooterCheckBox)
        self.ui.verticalLayout_2.insertLayout(log_index + 4, actions_layout)
        self.ui.verticalLayout_2.insertLayout(log_index + 5, logs_layout)
        self.recursiveBatchCheckBox.hide()

    def _setup_quit_action(self) -> None:
        # Ajoute une action "Quitter" avec le raccourci standard de la plateforme.
        self.quit_action = QAction("Quitter", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.ui.menuQuitter.addAction(self.quit_action)

    def _setup_donation_action(self) -> None:
        # Ajoute une entrée "Faire un don" dans le menu Aide.
        self.donation_action = QAction("Faire un don", self)
        self.ui.menuAide.addAction(self.donation_action)

    def _connect_signals(self) -> None:
        # Connecte les interactions UI aux méthodes métier.
        self.ui.browseUiButton.clicked.connect(self._browse_ui_file)
        self.ui.browseOutputDirButton.clicked.connect(self._browse_output_dir)
        self.ui.convertButton.clicked.connect(self._convert)
        self.ui.uiFileLineEdit.textChanged.connect(self._update_live_validation)
        self.ui.outputDirLineEdit.textChanged.connect(self._update_live_validation)
        self.ui.outputNameLineEdit.textChanged.connect(self._update_live_validation)
        self.ui.outputNameLineEdit.editingFinished.connect(self._autocorrect_output_name)
        self.batchModeCheckBox.stateChanged.connect(self._on_batch_mode_toggled)
        self.recursiveBatchCheckBox.stateChanged.connect(self._update_live_validation)
        self.ui.actionApropos.triggered.connect(self._show_about)
        self.donation_action.triggered.connect(self._open_donation_page)
        self.openGeneratedFileButton.clicked.connect(self._open_generated_file)
        self.openGeneratedFolderButton.clicked.connect(self._open_generated_folder)
        self.openDonationPageButton.clicked.connect(self._open_donation_page)
        self.copyLogsButton.clicked.connect(self._copy_logs_to_clipboard)
        self.clearLogsButton.clicked.connect(self._clear_logs)
        self.quit_action.triggered.connect(self.close)

    def _browse_ui_file(self) -> None:
        # Ouvre un sélecteur pour choisir le fichier .ui source ou un dossier en mode lot.
        if self.batchModeCheckBox.isChecked():
            selected_dir = QFileDialog.getExistingDirectory(
                self,
                "Choisir le dossier contenant les fichiers .ui",
                self.ui.uiFileLineEdit.text().strip() or str(Path.cwd()),
            )
            if not selected_dir:
                return

            input_dir = Path(selected_dir)
            self.ui.uiFileLineEdit.setText(str(input_dir))
            if not self.ui.outputDirLineEdit.text().strip():
                self.ui.outputDirLineEdit.setText(str(input_dir))
            if self.use_settings:
                self._settings.setValue("recent_ui_file", str(input_dir))
            self._log_info(f"Dossier source sélectionné: {input_dir}")
            return

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

        if self.use_settings:
            self._settings.setValue("recent_ui_file", str(ui_path))
        self._log_info(f"UI sélectionnée: {ui_path}")

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
        if self.use_settings:
            self._settings.setValue("recent_output_dir", str(output_dir))
        self._log_info(f"Dossier de sortie: {output_dir}")

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
        # Double garde: protège l'appel direct si le bouton est désactivé.
        blocking_errors, guidance_messages = self._compute_live_validation_feedback()
        if blocking_errors:
            self._apply_inline_validation(blocking_errors, guidance_messages)
            self._log_error(f"Validation bloquante: {blocking_errors[0]}")
            return

        if self.batchModeCheckBox.isChecked():
            input_dir = Path(self.ui.uiFileLineEdit.text().strip())
            output_dir_text = self.ui.outputDirLineEdit.text().strip()
            output_dir = Path(output_dir_text) if output_dir_text else None
            self._log_info(f"Conversion batch: {input_dir} -> {output_dir or 'même dossier'}")
            if self.use_settings:
                self._save_recent_values()
            self._set_conversion_in_progress(True)
            self._start_batch_conversion_worker(input_dir, output_dir)
            return

        ui_path = Path(self.ui.uiFileLineEdit.text().strip())
        output_path = self._build_output_path(ui_path)
        self._log_info(f"Chemin de sortie final calculé: {output_path}")

        # Demande confirmation si le fichier cible existe déjà.
        if output_path.exists():
            answer = QMessageBox.question(
                self,
                "Confirmer l'écrasement",
                f"Le fichier existe déjà:\n{output_path}\n\nVoulez-vous l'écraser ?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._log_info("Conversion annulée (écrasement refusé).")
                return

        if self.use_settings:
            self._save_recent_values()
        self._set_conversion_in_progress(True)
        self._start_conversion_worker(ui_path, output_path)

    def _start_batch_conversion_worker(self, input_dir: Path, output_dir: Path | None) -> None:
        include_preview_footer = self.previewFooterCheckBox.isChecked()
        recursive = self.recursiveBatchCheckBox.isChecked()
        self._conversion_thread = QThread(self)
        self._conversion_worker = BatchConversionWorker(
            input_dir=input_dir,
            output_dir=output_dir,
            recursive=recursive,
            include_preview_footer=include_preview_footer,
        )
        self._conversion_worker.moveToThread(self._conversion_thread)

        self._conversion_thread.started.connect(self._conversion_worker.run)
        self._conversion_worker.finished.connect(self._on_batch_conversion_finished)
        self._conversion_worker.failed.connect(self._on_conversion_failed)
        self._conversion_worker.finished.connect(self._conversion_thread.quit)
        self._conversion_worker.failed.connect(self._conversion_thread.quit)
        self._conversion_thread.finished.connect(self._cleanup_worker_thread)
        self._conversion_thread.finished.connect(self._conversion_worker.deleteLater)
        self._conversion_thread.finished.connect(self._conversion_thread.deleteLater)
        self._conversion_thread.start()

    def _start_conversion_worker(self, ui_path: Path, output_path: Path) -> None:
        include_preview_footer = self.previewFooterCheckBox.isChecked()
        self._conversion_thread = QThread(self)
        self._conversion_worker = ConversionWorker(
            ui_path=ui_path,
            output_path=output_path,
            include_preview_footer=include_preview_footer,
        )
        self._conversion_worker.moveToThread(self._conversion_thread)

        self._conversion_thread.started.connect(self._conversion_worker.run)
        self._conversion_worker.finished.connect(self._on_conversion_finished)
        self._conversion_worker.failed.connect(self._on_conversion_failed)
        self._conversion_worker.finished.connect(self._conversion_thread.quit)
        self._conversion_worker.failed.connect(self._conversion_thread.quit)
        self._conversion_thread.finished.connect(self._cleanup_worker_thread)
        self._conversion_thread.finished.connect(self._conversion_worker.deleteLater)
        self._conversion_thread.finished.connect(self._conversion_thread.deleteLater)
        self._conversion_thread.start()

    def _on_conversion_finished(self, output_path: Path, outcome) -> None:
        self._set_conversion_in_progress(False)
        if not outcome.success:
            if outcome.technical_details:
                LOGGER.error("Échec conversion: %s", outcome.technical_details)
                self._log_error(f"Détail technique: {outcome.technical_details}")
            self._show_error(outcome.user_message)
            return

        self._last_generated_path = output_path
        self.openGeneratedFileButton.setEnabled(output_path.exists())
        self.openGeneratedFolderButton.setEnabled(output_path.parent.exists())
        self._log_info(outcome.user_message)
        self.statusBar().showMessage("Conversion terminée", 5000)

    def _on_conversion_failed(self, message: str) -> None:
        LOGGER.exception("Worker de conversion en échec")
        self._set_conversion_in_progress(False)
        self._show_error(message)

    def _on_batch_conversion_finished(self, batch_outcome) -> None:
        self._set_conversion_in_progress(False)

        for ui_file, output_file, outcome in batch_outcome.outcomes:
            prefix = "INFO" if outcome.success else "ERREUR"
            self._log(prefix, f"{ui_file} -> {output_file}: {outcome.user_message}")
            if not outcome.success and outcome.technical_details:
                self._log_error(f"Détail technique ({ui_file.name}): {outcome.technical_details}")

        summary = (
            f"Batch terminé: {batch_outcome.success_count} succès, "
            f"{batch_outcome.failure_count} échec(s)."
        )
        self._log_info(summary)

        output_dir_text = self.ui.outputDirLineEdit.text().strip()
        if output_dir_text:
            candidate = Path(output_dir_text)
            if candidate.exists():
                self._last_generated_path = candidate
                self.openGeneratedFolderButton.setEnabled(True)

        if batch_outcome.failure_count > 0:
            self.statusBar().showMessage(summary, 7000)
            QMessageBox.warning(self, "Batch terminé avec erreurs", summary)
            return

        self.statusBar().showMessage(summary, 5000)

    def _cleanup_worker_thread(self) -> None:
        self._conversion_worker = None
        self._conversion_thread = None

    def _ask_close_confirmation(self) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "Quitter",
            "Voulez-vous vraiment quitter l'application ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

    def _should_confirm_close(self) -> bool:
        return self.confirm_on_close

    def _compute_live_validation_feedback(self) -> tuple[list[str], list[str]]:
        blocking_errors: list[str] = []
        guidance_messages: list[str] = []

        ui_path_text = self.ui.uiFileLineEdit.text().strip()
        if not ui_path_text:
            if self.batchModeCheckBox.isChecked():
                return ["Sélectionnez un dossier source contenant des fichiers .ui."], []
            return ["Sélectionnez un fichier .ui source."], []

        if self.batchModeCheckBox.isChecked():
            input_dir = Path(ui_path_text)
            if not input_dir.exists() or not input_dir.is_dir():
                return [f"Dossier source introuvable: {input_dir}"], []

            output_dir_text = self.ui.outputDirLineEdit.text().strip()
            if output_dir_text:
                output_dir = Path(output_dir_text)
                if output_dir.exists() and not output_dir.is_dir():
                    return [f"Le dossier de sortie est invalide: {output_dir}"], []

            return blocking_errors, guidance_messages

        ui_path = Path(ui_path_text)
        if not ui_path.exists():
            return [f"Fichier .ui introuvable: {ui_path}"], []
        if ui_path.suffix.lower() != ".ui":
            return ["Le fichier source doit avoir l'extension .ui."], []

        output_name_text = self.ui.outputNameLineEdit.text().strip()

        # Valide le nom de sortie selon les règles cross-plateforme s'il est fourni
        if output_name_text:
            output_name_errors = validate_output_filename_crossplatform(output_name_text)
            for message in output_name_errors:
                if "trailing" in message.lower():
                    guidance_messages.append(message)
                else:
                    blocking_errors.append(message)

        output_path = self._build_output_path(ui_path)
        validation_result = validate_before_conversion(ui_path, output_path)
        if not validation_result.is_valid:
            for message in validation_result.errors:
                if self._is_guidance_message(message):
                    guidance_messages.append(message)
                else:
                    blocking_errors.append(message)

        return blocking_errors, guidance_messages

    def _is_guidance_message(self, message: str) -> bool:
        lowered = message.lower()
        return (
            "widget custom" in lowered
            or "widgets custom" in lowered
            or "suppression automatique" in lowered
            or "renommé automatiquement" in lowered
        )

    def _apply_inline_validation(self, errors: list[str], guidance_messages: list[str]) -> None:
        if errors:
            first_error = errors[0]
            suffix = f" (+{len(errors) - 1} autre(s))" if len(errors) > 1 else ""
            self.ui.validationMessageLabel.setText(first_error + suffix)
            details = list(errors)
            if guidance_messages:
                details.append("")
                details.append("Aide:")
                details.extend(guidance_messages)
            self.ui.validationMessageLabel.setToolTip("\n".join(details))
            self.ui.validationMessageLabel.setStyleSheet("color: #c62828; font-size: 12px; font-weight: 500;")
            self.ui.validationMessageLabel.show()
            self.ui.convertButton.setEnabled(False)
            self.statusBar().showMessage("Entrées invalides")
            return

        if guidance_messages:
            first_message = guidance_messages[0]
            suffix = f" (+{len(guidance_messages) - 1} conseil(s))" if len(guidance_messages) > 1 else ""
            self.ui.validationMessageLabel.setText("Conseil: " + first_message + suffix)
            self.ui.validationMessageLabel.setToolTip("\n".join(guidance_messages))
            self.ui.validationMessageLabel.setStyleSheet("color: #8a5a00; font-size: 12px; font-weight: 500;")
            self.ui.validationMessageLabel.show()
            self.ui.convertButton.setEnabled(not self._is_converting)
            self.statusBar().showMessage("Prêt (avec conseils)")
            return

        if not errors and not guidance_messages:
            self.ui.validationMessageLabel.clear()
            self.ui.validationMessageLabel.hide()
            self.ui.validationMessageLabel.setToolTip("")
            self.ui.validationMessageLabel.setStyleSheet("color: #c62828; font-size: 12px; font-weight: 500;")
            self.ui.convertButton.setEnabled(not self._is_converting)
            self.statusBar().showMessage("Prêt")

    def _autocorrect_output_name(self) -> None:
        current_name = self.ui.outputNameLineEdit.text()
        if not current_name.strip():
            return

        suggested_name, messages = suggest_output_filename(current_name)
        if suggested_name != current_name:
            self.ui.outputNameLineEdit.blockSignals(True)
            self.ui.outputNameLineEdit.setText(suggested_name)
            self.ui.outputNameLineEdit.blockSignals(False)

        if messages:
            self._log_info(" ; ".join(messages))
            self.statusBar().showMessage("Nom de sortie ajusté automatiquement", 4000)

        self._update_live_validation()

    def _update_live_validation(self) -> None:
        blocking_errors, guidance_messages = self._compute_live_validation_feedback()
        self._apply_inline_validation(blocking_errors, guidance_messages)
        self._update_output_path_preview()

    def _on_batch_mode_toggled(self, *_args) -> None:
        is_batch_mode = self.batchModeCheckBox.isChecked()
        self.recursiveBatchCheckBox.setVisible(is_batch_mode)
        self.ui.outputNameLineEdit.setEnabled(not is_batch_mode)
        self.ui.labelOutName.setEnabled(not is_batch_mode)

        if is_batch_mode:
            self.ui.outputNameLineEdit.clear()
            self.ui.convertButton.setText("Convertir dossier .ui → .py")
            self.ui.groupBoxSource.setTitle("Dossier source (.ui)")
        else:
            self.ui.convertButton.setText("Convertir .ui → .py")
            self.ui.groupBoxSource.setTitle("Fichier source (.ui)")

        self._update_live_validation()

    def _set_conversion_in_progress(self, in_progress: bool) -> None:
        self._is_converting = in_progress
        if in_progress:
            self.ui.convertButton.setEnabled(False)
            self.previewFooterCheckBox.setEnabled(False)
            self.batchModeCheckBox.setEnabled(False)
            self.recursiveBatchCheckBox.setEnabled(False)
            self.ui.convertButton.setText("Conversion en cours...")
            self.statusBar().showMessage("Conversion en cours...")
            self._log_info("Conversion en cours...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            return

        self.ui.convertButton.setText(
            "Convertir dossier .ui → .py" if self.batchModeCheckBox.isChecked() else "Convertir .ui → .py"
        )
        self.previewFooterCheckBox.setEnabled(True)
        self.batchModeCheckBox.setEnabled(True)
        self.recursiveBatchCheckBox.setEnabled(self.batchModeCheckBox.isChecked())
        if QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        self._update_live_validation()

    def _update_output_path_preview(self) -> None:
        ui_path_text = self.ui.uiFileLineEdit.text().strip()
        if not ui_path_text:
            self.outputPathPreviewLabel.setText("Sortie finale: en attente")
            self.outputPathPreviewLabel.setToolTip("Renseignez un fichier .ui pour calculer le chemin final.")
            return

        if self.batchModeCheckBox.isChecked():
            input_dir = Path(ui_path_text)
            output_dir_text = self.ui.outputDirLineEdit.text().strip()
            if not input_dir.exists() or not input_dir.is_dir():
                self.outputPathPreviewLabel.setText("Sortie batch: dossier source invalide")
                self.outputPathPreviewLabel.setToolTip("Le mode batch attend un dossier source.")
                return

            output_dir = Path(output_dir_text) if output_dir_text else input_dir
            recursive_text = "avec sous-dossiers" if self.recursiveBatchCheckBox.isChecked() else "sans sous-dossiers"
            self.outputPathPreviewLabel.setText(
                f"Sortie batch: {output_dir} ({recursive_text})"
            )
            self.outputPathPreviewLabel.setToolTip(
                f"Les .ui de {input_dir} seront convertis vers {output_dir}."
            )
            return

        ui_path = Path(ui_path_text)
        if ui_path.suffix.lower() != ".ui":
            self.outputPathPreviewLabel.setText("Sortie finale: fichier source invalide")
            self.outputPathPreviewLabel.setToolTip("Le fichier source doit être un .ui.")
            return

        output_path = self._build_output_path(ui_path)
        self.outputPathPreviewLabel.setText(f"Sortie finale: {output_path}")
        self.outputPathPreviewLabel.setToolTip(str(output_path))

    def _open_generated_file(self) -> None:
        if self._last_generated_path is None or not self._last_generated_path.exists():
            self._show_error("Aucun fichier généré disponible à ouvrir.")
            return

        self._open_path(self._last_generated_path, "fichier généré")

    def _open_generated_folder(self) -> None:
        if self._last_generated_path is None:
            self._show_error("Aucun dossier de sortie disponible à ouvrir.")
            return

        output_dir = self._last_generated_path.parent
        if not output_dir.exists():
            self._show_error("Le dossier de sortie n'existe pas.")
            return

        self._open_path(output_dir, "dossier de sortie")

    def _open_path(self, path: Path, label: str) -> None:
        if QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            self._log_info(f"Ouverture du {label}: {path}")
            return

        self._show_error(f"Impossible d'ouvrir le {label}: {path}")

    def _open_donation_page(self) -> None:
        # Ouvre le lien de paiement Stripe partagé pour les dons.
        donation_url = QUrl(DONATION_PAYMENT_URL)
        if QDesktopServices.openUrl(donation_url):
            self._log_info(f"Ouverture de la page de don: {DONATION_PAYMENT_URL}")
            self.statusBar().showMessage("Page de don ouverte dans le navigateur", 4000)
            return

        self._show_error("Impossible d'ouvrir la page de don Stripe.")

    def _show_about(self) -> None:
        # Affiche une boîte d'information simple sur l'application.
        QMessageBox.information(
            self,
            "À propos",
            "Convertisseur UI → Python\nGénère des modules .py à partir de fichiers .ui (PySide6).",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Politique de fermeture centralisée pour simplifier les tests GUI.
        if not self._should_confirm_close():
            event.accept()
            return

        answer = self._ask_close_confirmation()
        if answer == QMessageBox.StandardButton.Yes:
            event.accept()
            return

        event.ignore()

    def _show_error(self, message: str) -> None:
        # Centralise l'affichage des erreurs (journal + barre d'état + popup).
        self._log_error(message)
        self.statusBar().showMessage("Erreur", 5000)
        QMessageBox.critical(self, "Erreur", message)

    def _copy_logs_to_clipboard(self) -> None:
        logs = self.ui.logTextEdit.toPlainText()
        QGuiApplication.clipboard().setText(logs)
        self.statusBar().showMessage("Logs copiés dans le presse-papiers", 3000)

    def _clear_logs(self) -> None:
        self.ui.logTextEdit.clear()
        self.statusBar().showMessage("Logs effacés", 3000)

    def _load_recent_values(self) -> None:
        recent_ui_file = self._settings.value("recent_ui_file", "", str)
        recent_output_dir = self._settings.value("recent_output_dir", "", str)

        if recent_ui_file:
            self.ui.uiFileLineEdit.setText(recent_ui_file)
        if recent_output_dir:
            self.ui.outputDirLineEdit.setText(recent_output_dir)

    def _save_recent_values(self) -> None:
        self._settings.setValue("recent_ui_file", self.ui.uiFileLineEdit.text().strip())
        self._settings.setValue("recent_output_dir", self.ui.outputDirLineEdit.text().strip())

    def _log(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ui.logTextEdit.append(f"[{timestamp}] [{level}] {message}")

    def _log_info(self, message: str) -> None:
        self._log("INFO", message)

    def _log_error(self, message: str) -> None:
        self._log("ERREUR", message)
