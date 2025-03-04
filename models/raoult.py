from models.equilibrium import EquilibriumModel
from constants import Constants

class RaoultModel(EquilibriumModel):
    def __init__(self, alpha=Constants.RELATIVE_VOLATILITY):
        self.alpha = alpha

    def calculate_y(self, x):
        return (self.alpha * x) / (1 + (self.alpha - 1) * x)

    def set_alpha(self, alpha):
        self.alpha = alpha
