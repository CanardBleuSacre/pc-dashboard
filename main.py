import sys
from pathlib import Path
from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtWidgets import (QApplication, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)
import core


class SizeWorker(QObject):
    finished = Signal(object)
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
    def run(self):
        try:
            self.finished.emit((core.directory_sizes(self.folder), None))
        except Exception as exc:
            self.finished.emit((None, str(exc)))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tableau de bord du PC')
        self.resize(800, 570)
        self.thread = None
        content = QWidget(); layout = QVBoxLayout(content)
        self.setCentralWidget(content)
        form = QFormLayout()
        self.disk_path = QLineEdit(str(Path.home()))
        self.report_path = QLineEdit(str(Path.home() / 'backup-report.json'))
        self.threshold = QSpinBox(); self.threshold.setRange(1, 99); self.threshold.setValue(15)
        self.age = QSpinBox(); self.age.setRange(1, 8760); self.age.setValue(48)
        form.addRow('Disque à surveiller (chemin) :', self.disk_path)
        form.addRow('Rapport de sauvegarde (JSON) :', self.report_path)
        form.addRow('Alerte espace libre sous (%) :', self.threshold)
        form.addRow('Alerte sauvegarde après (heures) :', self.age)
        layout.addLayout(form)
        refresh = QPushButton('Actualiser les indicateurs'); refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        self.storage = QLabel()
        self.backup = QLabel()
        self.warnings = QLabel()
        for label in (self.storage, self.backup, self.warnings):
            label.setWordWrap(True); layout.addWidget(label)
        bar = QHBoxLayout()
        self.folder = QLabel('Aucun dossier analysé')
        choose = QPushButton('Choisir un dossier à analyser'); choose.clicked.connect(self.choose)
        self.analyze = QPushButton('Calculer les tailles'); self.analyze.clicked.connect(self.scan)
        bar.addWidget(choose); bar.addWidget(self.analyze); layout.addLayout(bar)
        layout.addWidget(self.folder)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Sous-dossier', 'Taille'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.scan_folder = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(60_000)
        self.refresh()

    def refresh(self):
        try:
            disk = core.disk_info(self.disk_path.text().strip())
            backup = core.backup_status(self.report_path.text().strip())
            self.storage.setText(f"Stockage : {core.human(disk['used'])} utilisés / {core.human(disk['total'])} ; {core.human(disk['free'])} libres ({disk['free_percent']:.1f} %)")
            self.backup.setText('Sauvegarde : ' + (f"{backup['status']} — {backup['finished_at']} — {backup.get('copied', '?')} fichier(s) copiés" if backup else 'aucun rapport trouvé'))
            warnings = core.alerts(disk, backup, self.threshold.value(), self.age.value())
            self.warnings.setText('Alertes : ' + (' ; '.join(warnings) if warnings else 'aucune'))
        except (OSError, ValueError, KeyError) as exc:
            self.warnings.setText(f'Erreur de lecture : {exc}')

    def choose(self):
        folder = QFileDialog.getExistingDirectory(self, 'Dossier à analyser')
        if folder:
            self.scan_folder = folder
            self.folder.setText(folder)
            self.table.setRowCount(0)

    def scan(self):
        if not self.scan_folder:
            QMessageBox.information(self, 'Dossier', 'Choisis un dossier à analyser.'); return
        self.analyze.setEnabled(False)
        self.statusBar().showMessage('Calcul des tailles en cours…')
        self.thread = QThread()
        self.worker = SizeWorker(self.scan_folder)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.show_sizes)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def show_sizes(self, result):
        data, error = result
        self.analyze.setEnabled(True)
        if error:
            QMessageBox.warning(self, 'Analyse', error); return
        sizes, skipped = data
        self.table.setRowCount(len(sizes))
        for row, (name, size) in enumerate(sizes):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(core.human(size)))
        self.statusBar().showMessage(f'{len(sizes)} entrée(s), {skipped} fichier(s) ignoré(s)')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window(); window.show()
    sys.exit(app.exec())
