from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
from utils.energy_balance import calculate_energy_balance

class EnergyBalanceWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Balance Energético")
        self.setGeometry(200, 200, 600, 400)
        
        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Panel izquierdo: Entrada de datos
        input_panel = QVBoxLayout()
        input_panel.addWidget(QLabel("Entalpía de vaporización componente ligero (kJ/mol):"))
        self.hvap_light_input = QLineEdit("38.56")  # Valor por defecto: etanol
        input_panel.addWidget(self.hvap_light_input)

        input_panel.addWidget(QLabel("Entalpía de vaporización componente pesado (kJ/mol):"))
        self.hvap_heavy_input = QLineEdit("40.65")  # Valor por defecto: agua
        input_panel.addWidget(self.hvap_heavy_input)

        input_panel.addWidget(QLabel("Flujo de alimentación (mol/s):"))
        self.feed_flow_input = QLineEdit("1.0")  # Valor por defecto
        input_panel.addWidget(self.feed_flow_input)

        calc_btn = QPushButton("Calcular")
        calc_btn.clicked.connect(self.calculate_and_show)
        input_panel.addWidget(calc_btn)
        
        input_panel.addStretch()  # Espacio flexible para empujar los elementos arriba
        main_layout.addLayout(input_panel, stretch=1)

        # Panel derecho: Área para resultados y futuros dibujos
        result_panel = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_panel.addWidget(QLabel("Resultados:"))
        result_panel.addWidget(self.result_text)
        
        # Placeholder para un dibujo (puedes agregar un QCanvas o matplotlib aquí más adelante)
        self.drawing_area = QLabel("Área reservada para dibujo (pendiente)")
        self.drawing_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_panel.addWidget(self.drawing_area)
        
        main_layout.addLayout(result_panel, stretch=2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def calculate_and_show(self):
        try:
            hvap_light = float(self.hvap_light_input.text())
            hvap_heavy = float(self.hvap_heavy_input.text())
            feed_flow = float(self.feed_flow_input.text())
            if hvap_light <= 0 or hvap_heavy <= 0 or feed_flow <= 0:
                raise ValueError("Los valores deben ser positivos.")
            
            # Calcular el balance energético con los valores ingresados
            summary = calculate_energy_balance(self.parent, hvap_light, hvap_heavy, feed_flow)
            result_text = "\n".join(f"{k}: {v:.2f}" for k, v in summary.items())
            self.result_text.setText(result_text)
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Entrada inválida: {e}")
