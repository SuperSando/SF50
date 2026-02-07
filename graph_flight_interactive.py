import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION (KEPT FROM ORIGINAL) ---
GRAPH_MAPPINGS = {"Groundspeed": "Groundspeed", "Cabin Diff PSI": "Cabin Diff PSI", "Bld Px PSI": "Bld Px PSI", "Bleed On": "Bleed On", "N1 %": "N1 %", "N2 %": "N2 %", "ITT (F)": "ITT (F)", "Oil Temp (F)": "Oil Temp (F)", "Oil Px PSI": "Oil Px PSI", "TLA DEG": "TLA DEG", "TT2 (C)": "TT2 (C)", "PT2 PSI": "PT2 PSI", "CHPV": "CHPV", "ECS PRI DUCT T (F)": "ECS PRI DUCT T (F)", "ECS PRI DUCT T2 (F)": "ECS PRI DUCT T2 (F)", "ECS CKPT T (F)": "ECS CKPT T (F)", "O2 BTL Px PSI": "O2 BTL Px PSI", "O2 VLV Open": "O2 VLV Open", "EIPS TMP (F)": "EIPS TMP (F)", "EIPS PRS PSI": "EIPS PRS PSI"}
UNITS = {"Groundspeed": "kts", "Cabin Diff PSI": "psi", "Bld Px PSI": "psi", "Bleed On": "1=ON", "N1 %": "%", "N2 %": "%", "ITT (F)": "°F", "Oil Temp (F)": "°F", "Oil Px PSI": "psi", "TLA DEG": "°", "TT2 (C)": "°C", "PT2 PSI": "psi", "CHPV": "V", "ECS PRI DUCT T (F)": "°F", "ECS PRI DUCT T2 (F)": "°F", "ECS CKPT T (F)": "°F", "O2 BTL Px PSI": "psi", "O2 VLV Open": "1=OPEN", "EIPS TMP (F)": "°F", "EIPS PRS PSI": "psi"}
LIMIT_LINES = {"ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], "N1 %": [(105.7, "red", "Tran. 30sec"), (104.7, "green", "MCT")], "N2 %": [(101, "red", "Tran. 30sec"), (100, "green", "MCT")], "Oil Px PSI": [(120, "green", "max")]}
X_AXIS_COL = "Time"
BIG_NUMBER_THRESHOLD = 500

def generate_dashboard(df):
    """Refactored to accept a DataFrame and return a Plotly Figure."""
    # Cleanup Data types
    if X_AXIS_COL in df.columns:
         df[X_AXIS_COL] = pd.to_numeric(df[X_AXIS_COL], errors='coerce')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            max_val = df[col_name].max()
            use_secondary = not (max_val > BIG_NUMBER_THRESHOLD)
            unit = UNITS.get(title, "") 

            # Add Data Trace
            fig.add_trace(
                go.Scatter(x=df[X_AXIS_COL], y=df[col_name], name=title, mode='lines', 
                           visible='legendonly', legendgroup=title,
                           hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"),
                secondary_y=use_secondary, 
            )

            # Add Limit Lines
            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(x=[df[X_AXIS_COL].min(), df[X_AXIS_COL].max()], y=[val, val],
                                   mode='lines+text', text=[label, ""], textposition="top right",
                                   line=dict(color=color, width=1, dash='dash'),
                                   name=label, legendgroup=title, showlegend=False, 
                                   visible='legendonly', hoverinfo='skip'),
                        secondary_y=use_secondary 
                    )

    fig.update_layout(height=800, template="plotly_white", hovermode="x unified",
                      legend=dict(title="Click to Toggle:", y=0.99, x=1.05))
    return fig # Returns the figure to the app
