import numpy as np
from constants import Constants
from utils.calculations import q_line
from models.raoult import RaoultModel

def update_plot(window):
    from utils.calculations import update_intersection, is_point_valid
    update_intersection(window)
    window.point_outside = not is_point_valid(window)
    if not window.point_outside and not window.slider_active:
        window.valid_state = window.state.copy()
        if isinstance(window.current_model, RaoultModel):
            window.valid_alpha = window.current_model.alpha
    window.ax.clear()
    window.ax.set_xlim(*Constants.X_RANGE)
    window.ax.set_ylim(*Constants.Y_RANGE)
    window.ax.set_aspect('equal')
    window.ax.grid(True, color='lightgray')
    window.ax.set_xlabel("Fracción molar en líquido (x)")
    window.ax.set_ylabel("Fracción molar en vapor (y)")
    
    x_45 = np.linspace(Constants.X_RANGE[0], 1.0, 100)
    window.ax.plot(x_45, x_45, 'b-', label="y = x")
    x_eq = np.linspace(Constants.X_RANGE[0], 1.0, 100)
    y_eq = [window.current_model.calculate_y(x) for x in x_eq]
    window.ax.plot(x_eq, y_eq, 'r-', label="Curva de Equilibrio")
    x_q = np.linspace(*Constants.X_RANGE, 100)
    y_q = [q_line(window, x) for x in x_q]
    if abs(window.state['q'] - 1) < 1e-6:
        window.ax.vlines(window.state['zF'], Constants.Y_RANGE[0], Constants.Y_RANGE[1], 
                        colors='purple', label="Línea q")
    else:
        window.ax.plot(x_q, y_q, 'purple', label="Línea q")
    window.ax.plot([window.state['xD'], window.intersection['x']], 
                  [window.state['xD'], window.intersection['y']], 'g-', label="Rectificación")
    window.ax.plot([window.state['xB'], window.intersection['x']], 
                  [window.state['xB'], window.intersection['y']], 'orange', label="Agotamiento")
    window.ax.plot(window.intersection['x'], window.intersection['y'], 'yo', label="Intersección")
    for p, label in [(window.state['xB'], "xB"), (window.state['zF'], "xF"), (window.state['xD'], "xD")]:
        window.ax.plot(p, p, 'ro', label=label)
    
    if window.stages_calculated and not window.point_outside:
        for i in range(0, len(window.stages_horiz), 2):
            x_vals, y_vals = zip(window.stages_horiz[i], window.stages_horiz[i+1])
            window.ax.plot(x_vals, y_vals, 'k-', linewidth=1)
        for i in range(0, len(window.stages_vert), 2):
            x_vals, y_vals = zip(window.stages_vert[i], window.stages_vert[i+1])
            window.ax.plot(x_vals, y_vals, 'k-', linewidth=1)
    
    window.ax.legend(loc='lower right', bbox_to_anchor=(1.1, 0), 
                    bbox_transform=window.ax.transData, borderaxespad=0., fontsize=10)
    window.canvas.draw()
    log = f"Etapas: {len(window.stages_table)} Último x: {window.state['xB']:.2f}"
    if window.point_outside:
        log += " (Sin solución)"
    window.log_text.setText(log)
