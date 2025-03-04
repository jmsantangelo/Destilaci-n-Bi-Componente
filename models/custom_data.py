import numpy as np
from scipy.interpolate import interp1d
from models.equilibrium import EquilibriumModel

class CustomDataModel(EquilibriumModel):
    def __init__(self, x_data, y_data):
        self.x_data = np.array(x_data)
        self.y_data = np.array(y_data)
        self.interp = interp1d(self.x_data, self.y_data, kind='linear', fill_value="extrapolate")

    def calculate_y(self, x):
        return self.interp(x)
