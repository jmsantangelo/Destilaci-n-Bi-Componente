from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QPushButton, QTextEdit, QMenu)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from constants import Constants
from models.raoult import RaoultModel
from ui.dialogs import MixtureSelectionDialog, CustomDataDialog, WarningDialog
from ui.energy_balance_window import EnergyBalanceWindow
from utils.calculations import (update_intersection, calculate_stages, calculate_rmin, 
                               is_point_valid, q_line, find_curve_intersection)
from utils.plotting import update_plot

class DistillationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Destilación de 2 Componentes")
        self.setGeometry(100, 100, 1160, 860)
        
        self.state = Constants.INITIAL_VALUES.copy()
        self.valid_state = self.state.copy()
        self.valid_alpha = Constants.RELATIVE_VOLATILITY
        self.intersection = {'x': 0, 'y': 0}
        self.stages_calculated = False
        self.stages_horiz = []
        self.stages_vert = []
        self.stages_table = []
        self.point_outside = False
        self.slider_active = False
        self.rmin = None
        self.current_model = RaoultModel()
        
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.set_aspect('equal')
        self.canvas = FigureCanvas(self.fig)
        
        self._setup_menu()
        self._setup_ui()
        update_plot(self)

    def _setup_menu(self):
        menu_bar = self.menuBar()
        # Menú Termodinámica
        thermo_menu = menu_bar.addMenu("Termodinámica")
        raoult_action = thermo_menu.addAction("Ley de Raoult (ideal)")
        raoult_action.triggered.connect(lambda: self.set_model(RaoultModel()))
        peng_robinson_action = thermo_menu.addAction("Peng-Robinson")
        peng_robinson_action.triggered.connect(self.open_peng_robinson_dialog)
        custom_data_action = thermo_menu.addAction("Datos Personalizados")
        custom_data_action.triggered.connect(self.open_custom_data_dialog)
        # Menú Balance
        balance_menu = menu_bar.addMenu("Balance")
        energy_action = balance_menu.addAction("Energía")
        energy_action.triggered.connect(self.open_energy_balance_window)
        mass_action = balance_menu.addAction("Masa")
        mass_action.triggered.connect(self._placeholder_mass_balance)

    def _setup_ui(self):
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        self._create_sliders(left_panel)
        left_panel.addSpacing(20)
        self._create_buttons(left_panel)
        main_layout.addLayout(left_panel, stretch=1)
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas, stretch=4)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(40)
        graph_layout.addWidget(self.log_text)
        main_layout.addLayout(graph_layout, stretch=4)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _create_sliders(self, layout):
        sliders_config = [
            ('R', 'Relación de Reflujo', 5, 500),
            ('q', 'Parámetro de Alimentación', -200, 300),
            ('xD', 'Fracción molar destilado', 70, 95),
            ('zF', 'Fracción molar alimentación', 27, 63),
            ('xB', 'Fracción molar fondo', 5, 25),
            ('alpha', 'Volatilidad Relativa', 100, 500)
        ]
        self.sliders = {}
        self.slider_labels = {}
        for param, label_text, min_val, max_val in sliders_config:
            slider_layout = QVBoxLayout()
            slider_layout.setSpacing(0)
            slider_layout.setContentsMargins(0, 0, 0, 2)
            initial_value = self.state.get(param, Constants.RELATIVE_VOLATILITY if param == 'alpha' else 0)
            label = QLabel(f"{label_text}: {initial_value:.2f}")
            slider_layout.addWidget(label)
            self.slider_labels[param] = label
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(int(initial_value * 100))
            slider.setSingleStep(1)
            slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            slider.valueChanged.connect(lambda v, p=param: self._update_param(p, v))
            slider.sliderPressed.connect(self._slider_pressed)
            slider.sliderReleased.connect(self._slider_released)
            if param == 'alpha':
                slider.setEnabled(isinstance(self.current_model, RaoultModel))
            slider_layout.addWidget(slider)
            layout.addLayout(slider_layout)
            self.sliders[param] = slider

    def _create_buttons(self, layout):
        buttons = [
            ('Cálculo de Rmin', lambda: calculate_rmin(self)),
            ('Reset', self._reset),
            ('Etapas', self._calculate_and_plot_stages),
            ('Exportar Informe', self._export_report),
            ('PDF', self._export_pdf),
        ]
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        self.rmin_label = QLabel("Rmin: -")
        layout.addWidget(self.rmin_label)

    def _slider_pressed(self):
        self.slider_active = True

    def _slider_released(self):
        self.slider_active = False
        update_intersection(self)
        self.point_outside = not is_point_valid(self)
        if self.stages_calculated:
            calculate_stages(self)
        if self.point_outside:
            WarningDialog(self, self._revert_to_valid).exec()
        update_plot(self)

    def _update_param(self, param, value):
        value = value / 100
        if param == 'alpha' and isinstance(self.current_model, RaoultModel):
            self.current_model.set_alpha(value)
        else:
            self.state[param] = value
        label_text = self.slider_labels[param].text().split(":")[0]
        self.slider_labels[param].setText(f"{label_text}: {value:.2f}")
        if self.stages_calculated:
            calculate_stages(self)
        update_plot(self)

    def _calculate_and_plot_stages(self):
        calculate_stages(self)
        update_plot(self)

    def _reset(self):
        self.state = Constants.INITIAL_VALUES.copy()
        for param, slider in self.sliders.items():
            if param == 'alpha' and isinstance(self.current_model, RaoultModel):
                slider.setValue(int(Constants.RELATIVE_VOLATILITY * 100))
                self.current_model.set_alpha(Constants.RELATIVE_VOLATILITY)
                self.valid_alpha = Constants.RELATIVE_VOLATILITY
                self.slider_labels[param].setText(f"Volatilidad Relativa: {Constants.RELATIVE_VOLATILITY:.2f}")
            elif param != 'alpha':
                slider.setValue(int(self.state[param] * 100))
                label_text = self.slider_labels[param].text().split(":")[0]
                self.slider_labels[param].setText(f"{label_text}: {self.state[param]:.2f}")
        self.sliders['alpha'].setEnabled(isinstance(self.current_model, RaoultModel))
        self.stages_calculated = False
        self.stages_horiz.clear()
        self.stages_vert.clear()
        self.stages_table.clear()
        self.rmin = None
        self.rmin_label.setText("Rmin: -")
        update_plot(self)

    def _export_report(self):
        from PyQt6.QtWidgets import QFileDialog
        import pandas as pd
        if not self.stages_calculated or self.point_outside:
            return
        df = pd.DataFrame([vars(stage) for stage in self.stages_table])
        file, _ = QFileDialog.getSaveFileName(self, "Guardar Informe", "", "CSV files (*.csv)")
        if file:
            df.to_csv(file, index=False)
            print(f"Informe exportado a: {file}")

    def _export_pdf(self):
        from PyQt6.QtWidgets import QFileDialog
        file, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "", "PDF files (*.pdf)")
        if file:
            self.fig.savefig(file)
            print(f"PDF exportado a: {file}")

    def _revert_to_valid(self):
        self.state = self.valid_state.copy()
        for param, slider in self.sliders.items():
            if param == 'alpha' and isinstance(self.current_model, RaoultModel):
                slider.setValue(int(self.valid_alpha * 100))
                self.current_model.set_alpha(self.valid_alpha)
                self.slider_labels[param].setText(f"Volatilidad Relativa: {self.valid_alpha:.2f}")
            elif param != 'alpha':
                slider.setValue(int(self.state[param] * 100))
                label_text = self.slider_labels[param].text().split(":")[0]
                self.slider_labels[param].setText(f"{label_text}: {self.state[param]:.2f}")
        self.sliders['alpha'].setEnabled(isinstance(self.current_model, RaoultModel))
        self.stages_calculated = False
        self.stages_horiz.clear()
        self.stages_vert.clear()
        self.stages_table.clear()
        update_plot(self)

    def open_peng_robinson_dialog(self):
        from models.peng_robinson import PengRobinsonModel
        dialog = MixtureSelectionDialog(self)
        if dialog.exec():
            mixture = dialog.get_mixture()
            self.set_model(PengRobinsonModel(mixture=mixture))

    def open_custom_data_dialog(self):
        from models.custom_data import CustomDataModel
        dialog = CustomDataDialog(self)
        if dialog.exec():
            try:
                x_data, y_data = dialog.get_data()
                if x_data and y_data:
                    self.set_model(CustomDataModel(x_data, y_data))
            except ValueError as e:
                print(f"Error al procesar datos: {e}")

    def set_model(self, model):
        from models.custom_data import CustomDataModel
        if isinstance(self.current_model, CustomDataModel) and isinstance(model, RaoultModel):
            self._reset()
        self.current_model = model
        self.sliders['alpha'].setEnabled(isinstance(self.current_model, RaoultModel))
        if isinstance(self.current_model, RaoultModel):
            self.sliders['alpha'].setValue(int(self.current_model.alpha * 100))
            self.slider_labels['alpha'].setText(f"Volatilidad Relativa: {self.current_model.alpha:.2f}")
            self.valid_alpha = self.current_model.alpha
        self.stages_calculated = False
        update_plot(self)

    def open_energy_balance_window(self):
        self.energy_window = EnergyBalanceWindow(self)
        self.energy_window.show()

    def _placeholder_mass_balance(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Balance de Masa", "Funcionalidad aún no implementada.")
