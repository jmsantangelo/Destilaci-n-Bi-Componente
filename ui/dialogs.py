from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, 
                             QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QLabel)
from PyQt6.QtCore import Qt
import pandas as pd

class MixtureSelectionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Mezcla")
        layout = QVBoxLayout()
        self.combo = QComboBox()
        self.combo.addItems(["ethanol-water", "otra-mezcla"])
        layout.addWidget(self.combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_mixture(self):
        return self.combo.currentText()

class CustomDataDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Ingresar Datos de Equilibrio")
        layout = QVBoxLayout()
        self.table = QTableWidget(100, 2)
        self.table.setHorizontalHeaderLabels(["x", "y"])
        layout.addWidget(self.table)
        import_btn = QPushButton("Importar CSV")
        import_btn.clicked.connect(self.import_csv)
        layout.addWidget(import_btn)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def import_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir archivo CSV", "", "CSV files (*.csv)")
        if file_name:
            try:
                df = pd.read_csv(file_name)
                if 'x' not in df.columns or 'y' not in df.columns:
                    raise ValueError("El archivo CSV debe tener columnas 'x' y 'y'.")
                x_data = df['x'].dropna().tolist()
                y_data = df['y'].dropna().tolist()
                if len(x_data) > 100 or len(y_data) > 100:
                    x_data = x_data[:100]
                    y_data = y_data[:100]
                for row in range(min(len(x_data), len(y_data))):
                    self.table.setItem(row, 0, QTableWidgetItem(str(x_data[row])))
                    self.table.setItem(row, 1, QTableWidgetItem(str(y_data[row])))
            except Exception as e:
                print(f"Error al importar CSV: {e}")

    def get_data(self):
        x_data = []
        y_data = []
        for row in range(self.table.rowCount()):
            x_item = self.table.item(row, 0)
            y_item = self.table.item(row, 1)
            if x_item and y_item:
                try:
                    x_val = float(x_item.text())
                    y_val = float(y_item.text())
                    x_data.append(x_val)
                    y_data.append(y_val)
                except ValueError:
                    pass
        if len(x_data) < 2 or len(y_data) < 2:
            raise ValueError("Se necesitan al menos 2 puntos válidos para ajustar la curva.")
        return x_data, y_data

class WarningDialog(QDialog):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.setWindowTitle("Advertencia")
        self.setModal(True)
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Sin solución posible", alignment=Qt.AlignmentFlag.AlignCenter))
        btn = QPushButton("Volver")
        btn.clicked.connect(callback)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)
