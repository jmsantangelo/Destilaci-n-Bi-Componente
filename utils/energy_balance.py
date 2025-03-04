import numpy as np
from constants import Constants

class EnergyBalance:
    def __init__(self, window, hvap_light, hvap_heavy, feed_flow):
        self.window = window
        self.Hvap_light = hvap_light  # Entalpía del componente ligero (kJ/mol)
        self.Hvap_heavy = hvap_heavy  # Entalpía del componente pesado (kJ/mol)
        self.F = feed_flow           # Flujo de alimentación (mol/s)

    def calculate_flows(self):
        zF = self.window.state['zF']
        xD = self.window.state['xD']
        xB = self.window.state['xB']
        D = (zF - xB) / (xD - xB) * self.F
        B = self.F - D
        return self.F, D, B

    def calculate_reboiler_heat(self):
        _, D, B = self.calculate_flows()
        R = self.window.state['R']
        V = (R + 1) * D
        xB = self.window.state['xB']
        Hvap_avg = xB * self.Hvap_heavy + (1 - xB) * self.Hvap_light
        Q_R = V * Hvap_avg  # kJ/s
        return Q_R

    def calculate_condenser_heat(self):
        _, D, _ = self.calculate_flows()
        R = self.window.state['R']
        V = (R + 1) * D
        xD = self.window.state['xD']
        Hvap_avg = xD * self.Hvap_light + (1 - xD) * self.Hvap_heavy
        Q_C = V * Hvap_avg  # kJ/s
        return Q_C

    def get_energy_summary(self):
        Q_R = self.calculate_reboiler_heat()
        Q_C = self.calculate_condenser_heat()
        F, D, B = self.calculate_flows()
        summary = {
            'Feed Flow (F, mol/s)': F,
            'Distillate Flow (D, mol/s)': D,
            'Bottoms Flow (B, mol/s)': B,
            'Reboiler Heat (Q_R, kJ/s)': Q_R,
            'Condenser Heat (Q_C, kJ/s)': Q_C,
            'Energy Ratio (Q_R/Q_C)': Q_R / Q_C if Q_C != 0 else float('inf')
        }
        return summary

def calculate_energy_balance(window, hvap_light=38.56, hvap_heavy=40.65, feed_flow=1.0):
    eb = EnergyBalance(window, hvap_light, hvap_heavy, feed_flow)
    return eb.get_energy_summary()
