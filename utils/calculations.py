import numpy as np
from scipy.optimize import fsolve
from constants import Constants
from models.raoult import RaoultModel
from models.equilibrium import StageData

def q_line(window, x):
    if abs(window.state['q'] - 1) < 1e-6:
        return window.state['zF']
    slope = window.state['q'] / (window.state['q'] - 1)
    intercept = -window.state['zF'] / (window.state['q'] - 1)
    return slope * x + intercept

def update_intersection(window):
    R, q, xD, zF = window.state['R'], window.state['q'], window.state['xD'], window.state['zF']
    if abs(q - 1) < 1e-6:
        window.intersection['x'] = zF
        window.intersection['y'] = (R / (R + 1)) * zF + (xD / (R + 1))
    else:
        slope_q = q / (q - 1)
        intercept_q = -zF / (q - 1)
        slope_rect = R / (R + 1)
        intercept_rect = xD / (R + 1)
        denom = slope_q - slope_rect
        if abs(denom) < 1e-6:
            window.intersection['x'] = zF
            window.intersection['y'] = q_line(window, zF)
        else:
            window.intersection['x'] = (intercept_rect - intercept_q) / (slope_q - slope_rect)
            window.intersection['y'] = q_line(window, window.intersection['x'])
    window.intersection['x'] = np.clip(window.intersection['x'], *Constants.X_RANGE)
    window.intersection['y'] = np.clip(window.intersection['y'], *Constants.Y_RANGE)
    if not window.point_outside and not window.slider_active and isinstance(window.current_model, RaoultModel):
        window.valid_alpha = window.current_model.alpha

def is_point_valid(window):
    x, y = window.intersection['x'], window.intersection['y']
    y_eq = window.current_model.calculate_y(x)
    return (window.state['xB'] <= x <= window.state['xD']) and (y <= y_eq)

def calculate_stages(window):
    window.stages_calculated = True
    window.stages_horiz.clear()
    window.stages_vert.clear()
    window.stages_table.clear()
    x, y = window.state['xD'], window.state['xD']
    stage = 0
    xB_threshold = window.state['xB'] * 1.05
    while x > xB_threshold and stage < 100:
        x_out = x
        y_out = window.current_model.calculate_y(x_out)
        y_out = np.clip(y_out, *Constants.Y_RANGE)
        if abs(y_out - y) > 1e-3:
            if isinstance(window.current_model, RaoultModel):
                a = window.current_model.alpha - (window.current_model.alpha - 1) * y
                x_out = y / a if abs(a) > 1e-4 else 0
                y_out = y
            else:
                def func(x):
                    return window.current_model.calculate_y(x) - y
                x_out, = fsolve(func, x)
                y_out = y
        x_out = np.clip(x_out, *Constants.X_RANGE)
        window.stages_horiz.extend([(x, y), (x_out, y_out)])
        if x_out > window.intersection['x']:
            y_new = (window.state['R'] / (window.state['R'] + 1)) * x_out + (window.state['xD'] / (window.state['R'] + 1))
        else:
            if x_out <= window.state['xB']:
                y_new = x_out
            else:
                m = (window.intersection['y'] - window.state['xB']) / (window.intersection['x'] - window.state['xB'])
                b = window.intersection['y'] - m * window.intersection['x']
                y_new = m * x_out + b
        y_new = np.clip(y_new, *Constants.Y_RANGE)
        window.stages_vert.extend([(x_out, y_out), (x_out, y_new)])
        stage += 1
        window.stages_table.append(StageData(stage, x, y_out, x_out, y_new))
        x, y = x_out, y_new

def calculate_rmin(window):
    x_int = find_curve_intersection(window)
    y_int = window.current_model.calculate_y(x_int)
    Rmin = (y_int - window.state['xD']) / (x_int - window.state['xD']) / (1 - (y_int - window.state['xD']) / (x_int - window.state['xD']))
    window.rmin = Rmin
    window.state['R'] = Rmin
    window.sliders['R'].setValue(int(Rmin * 100))
    window.rmin_label.setText(f"Rmin: {Rmin:.2f}")
    label_text = window.slider_labels['R'].text().split(":")[0]
    window.slider_labels['R'].setText(f"{label_text}: {window.state['R']:.2f}")

def find_curve_intersection(window):
    q = window.state['q']
    if abs(q - 1) < 1e-6:
        return window.state['zF']
    def func(x):
        y_q = q_line(window, x)
        y_eq = window.current_model.calculate_y(x)
        return y_q - y_eq
    x_sol, = fsolve(func, window.state['zF'])
    return np.clip(x_sol, *Constants.X_RANGE)
