from dataclasses import dataclass

@dataclass
class StageData:
    number: int
    x_in: float
    y_out: float
    x_out: float
    y_in: float

class EquilibriumModel:
    def calculate_y(self, x):
        raise NotImplementedError("Este método debe ser implementado por las subclases")
