# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'convertisseur.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(680, 580)
        MainWindow.setStyleSheet(u"\n"
"/* Style g\u00e9n\u00e9ral : fond macOS */\n"
"QMainWindow, QWidget#centralwidget {\n"
"    background-color: #f5f5f7;\n"
"}\n"
"\n"
"/* GroupBox arrondis style macOS */\n"
"QGroupBox {\n"
"    font-weight: 500;\n"
"    border: 1px solid #d9d9e3;\n"
"    border-radius: 12px;\n"
"    margin-top: 1.5ex;\n"
"    padding-top: 0.5ex;\n"
"    background-color: #ffffff;\n"
"    font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    left: 16px;\n"
"    padding: 0 8px 0 8px;\n"
"    color: #1c1c1e;\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"/* LineEdit style Mac */\n"
"QLineEdit {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #c6c6c8;\n"
"    border-radius: 8px;\n"
"    padding: 6px 10px;\n"
"    font-size: 13px;\n"
"    selection-background-color: #007aff;\n"
"}\n"
"QLineEdit:focus {\n"
"    border: 1px solid #007aff;\n"
"}\n"
"QLineEdit:hover {\n"
"    border: 1px solid #8e8e93;\n"
"}\n"
""
                        "\n"
"/* Bouton principal d\u00e9grad\u00e9 */\n"
"QPushButton#convertButton {\n"
"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n"
"                                stop:0 #007aff, stop:1 #005fcb);\n"
"    color: white;\n"
"    border: none;\n"
"    border-radius: 8px;\n"
"    padding: 8px 16px;\n"
"    font-weight: 600;\n"
"    font-size: 13px;\n"
"}\n"
"QPushButton#convertButton:hover {\n"
"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n"
"                                stop:0 #0a84ff, stop:1 #0040b3);\n"
"}\n"
"QPushButton#convertButton:pressed {\n"
"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,\n"
"                                stop:0 #005fcb, stop:1 #00309c);\n"
"}\n"
"\n"
"/* Boutons secondaires (Parcourir) */\n"
"QPushButton#secondaryButton {\n"
"    background: #e9e9ef;\n"
"    color: #1c1c1e;\n"
"    border: 1px solid #d4d4dc;\n"
"    border-radius: 8px;\n"
"}\n"
"QPushButton#secondaryButton:hover {\n"
"    background: #dfdfe6;\n"
"}\n"
"QPushButton#secondaryButton:pres"
                        "sed {\n"
"    background: #d1d1d9;\n"
"}\n"
"\n"
"/* Zone de logs monospace arrondie */\n"
"QTextEdit#logTextEdit {\n"
"    background-color: #fefefe;\n"
"    border: 1px solid #d9d9e3;\n"
"    border-radius: 12px;\n"
"    font-family: 'SF Mono', 'Menlo', monospace;\n"
"    font-size: 12px;\n"
"    padding: 8px;\n"
"    color: #1c1c1e;\n"
"}\n"
"QTextEdit#logTextEdit:focus {\n"
"    border: 1px solid #007aff;\n"
"}\n"
"\n"
"/* Barre de statut */\n"
"QStatusBar {\n"
"    background-color: #f5f5f7;\n"
"    color: #6c6c70;\n"
"    font-size: 11px;\n"
"}\n"
"QLabel {\n"
"    color: #2c2c2e;\n"
"    font-size: 13px;\n"
"}\n"
"QMenuBar {\n"
"    background-color: #f5f5f7;\n"
"    color: #1c1c1e;\n"
"    font-weight: 500;\n"
"}\n"
"QMenuBar::item:selected {\n"
"    background-color: #e6e6ed;\n"
"    border-radius: 4px;\n"
"}\n"
"QMenu {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #d9d9e3;\n"
"    border-radius: 8px;\n"
"}\n"
"QMenu::item:selected {\n"
"    background-color: #007aff;\n"
"    color: wh"
                        "ite;\n"
"}\n"
"   ")
        self.actionApropos = QAction(MainWindow)
        self.actionApropos.setObjectName(u"actionApropos")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(16)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.groupBoxSource = QGroupBox(self.centralwidget)
        self.groupBoxSource.setObjectName(u"groupBoxSource")
        self.horizontalLayout_2 = QHBoxLayout(self.groupBoxSource)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.uiFileLineEdit = QLineEdit(self.groupBoxSource)
        self.uiFileLineEdit.setObjectName(u"uiFileLineEdit")

        self.horizontalLayout_2.addWidget(self.uiFileLineEdit)

        self.browseUiButton = QPushButton(self.groupBoxSource)
        self.browseUiButton.setObjectName(u"browseUiButton")

        self.horizontalLayout_2.addWidget(self.browseUiButton)


        self.verticalLayout_2.addWidget(self.groupBoxSource)

        self.groupBoxDest = QGroupBox(self.centralwidget)
        self.groupBoxDest.setObjectName(u"groupBoxDest")
        self.verticalLayout = QVBoxLayout(self.groupBoxDest)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.labelOutDir = QLabel(self.groupBoxDest)
        self.labelOutDir.setObjectName(u"labelOutDir")

        self.horizontalLayout.addWidget(self.labelOutDir)

        self.outputDirLineEdit = QLineEdit(self.groupBoxDest)
        self.outputDirLineEdit.setObjectName(u"outputDirLineEdit")

        self.horizontalLayout.addWidget(self.outputDirLineEdit)

        self.browseOutputDirButton = QPushButton(self.groupBoxDest)
        self.browseOutputDirButton.setObjectName(u"browseOutputDirButton")

        self.horizontalLayout.addWidget(self.browseOutputDirButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.labelOutName = QLabel(self.groupBoxDest)
        self.labelOutName.setObjectName(u"labelOutName")

        self.horizontalLayout_3.addWidget(self.labelOutName)

        self.outputNameLineEdit = QLineEdit(self.groupBoxDest)
        self.outputNameLineEdit.setObjectName(u"outputNameLineEdit")

        self.horizontalLayout_3.addWidget(self.outputNameLineEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.verticalLayout_2.addWidget(self.groupBoxDest)

        self.convertButton = QPushButton(self.centralwidget)
        self.convertButton.setObjectName(u"convertButton")
        self.convertButton.setMinimumHeight(42)

        self.verticalLayout_2.addWidget(self.convertButton)

        self.logTextEdit = QTextEdit(self.centralwidget)
        self.logTextEdit.setObjectName(u"logTextEdit")
        self.logTextEdit.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.logTextEdit)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 680, 24))
        self.menuAide = QMenu(self.menubar)
        self.menuAide.setObjectName(u"menuAide")
        self.menuQuitter = QMenu(self.menubar)
        self.menuQuitter.setObjectName(u"menuQuitter")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuAide.menuAction())
        self.menubar.addAction(self.menuQuitter.menuAction())
        self.menuAide.addAction(self.actionApropos)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Convertisseur UI \u2192 Python \u2013 ", None))
        self.actionApropos.setText(QCoreApplication.translate("MainWindow", u"\u00c0 propos", None))
        self.groupBoxSource.setTitle(QCoreApplication.translate("MainWindow", u"Fichier source (.ui)", None))
        self.uiFileLineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Chemin vers le fichier .ui (ex: interface.ui)", None))
        self.browseUiButton.setText(QCoreApplication.translate("MainWindow", u"Parcourir...", None))
        self.browseUiButton.setObjectName(QCoreApplication.translate("MainWindow", u"secondaryButton", None))
        self.groupBoxDest.setTitle(QCoreApplication.translate("MainWindow", u"Destination (.py)", None))
        self.labelOutDir.setText(QCoreApplication.translate("MainWindow", u"Dossier de sortie :", None))
        self.outputDirLineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Dossier o\u00f9 sera g\u00e9n\u00e9r\u00e9 le fichier .py", None))
        self.browseOutputDirButton.setText(QCoreApplication.translate("MainWindow", u"Parcourir...", None))
        self.browseOutputDirButton.setObjectName(QCoreApplication.translate("MainWindow", u"secondaryButton", None))
        self.labelOutName.setText(QCoreApplication.translate("MainWindow", u"Nom du fichier .py :", None))
        self.outputNameLineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"ex: mon_ui (sans extension)", None))
        self.convertButton.setText(QCoreApplication.translate("MainWindow", u"Convertir .ui \u2192 .py", None))
        self.convertButton.setObjectName(QCoreApplication.translate("MainWindow", u"convertButton", None))
        self.logTextEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Les messages de conversion s'afficheront ici...", None))
        self.logTextEdit.setObjectName(QCoreApplication.translate("MainWindow", u"logTextEdit", None))
        self.menuAide.setTitle(QCoreApplication.translate("MainWindow", u"Aide", None))
        self.menuQuitter.setTitle(QCoreApplication.translate("MainWindow", u"Quitter", None))
    # retranslateUi

