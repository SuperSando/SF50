import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION ---
GRAPH_MAPPINGS = {
    "Groundspeed": "Groundspeed", "Cabin Diff PSI": "Cabin Diff PSI", 
    "Bld Px PSI": "Bld Px PSI", "Bleed On": "Bleed On", "N1 %": "N1 %", 
    "N2 %": "N2 %", "ITT (F)": "ITT (F)", "Oil Temp (F)": "Oil Temp (F)", 
    "Oil Px PSI": "Oil Px PSI", "TLA DEG": "TLA DEG", "TT2 (C)": "TT2 (C)", 
    "PT2 PSI": "PT2 PSI", "CHPV": "CHPV", "ECS PRI DUCT T (F)": "ECS PRI DUCT T (F)", 
    "ECS PRI DUCT T2 (F)": "ECS PRI DUCT T2 (F)", "ECS CKPT T (F)": "ECS CKPT T (F)", 
    "O2 BTL Px PSI": "O2 BTL Px PSI", "O2 VLV Open": "O2 VLV Open", 
    "EIPS TMP (F)": "EIPS TMP (F)", "EIPS PRS PSI": "EIPS PRS PSI"
}

# Parameters visible on load
DEFAULT_VISIBLE = ["ITT (F)", "N1 %", "Groundspeed"]

UNITS = {
    "Groundspeed": "kts", "Cabin Diff PSI": "psi", "Bld Px PSI": "psi", 
    "Bleed On": "1=ON", "N1 %": "%", "N2 %": "%", "ITT (F)": "°F", 
    "Oil Temp (F)": "°F", "Oil Px PSI": "psi", "TLA DEG": "°", "TT2 (C)": "°C", 
    "PT2 PSI": "psi", "CHPV": "V", "ECS PRI DUCT T (F)": "°F", 
    "ECS PRI DUCT T2 (F)": "°F", "ECS CKPT T (F)": "°F", 
    "O2 BTL Px PSI": "psi", "O2 VLV Open": "1=OPEN", "EIPS TMP (F)": "°F", 
    "EIPS PRS PSI": "psi"
}

LIMIT_LINES = {
    "ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], 
    "N1 %": [(105.7, "red", "Tran. 30sec"), (104.7, "green", "MCT")], 
    "N2 %": [(101, "red", "Tran. 30sec"), (100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

X_AXIS_COL = "Time"
BIG_NUMBER_THRESHOLD = 500

def generate_dashboard(df):
    if X_AXIS_COL in df.columns:
         df[X_AXIS_COL] = pd.to_numeric(df[X_AXIS_COL], errors='coerce')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Plotly default color cycle to match annotations to line colors
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            max_val = df[col_name].max()
            use_secondary = not (max_val > BIG_NUMBER_THRESHOLD)
            unit = UNITS.get(title, "") 
            line_color = colors[color_idx % len(colors)]
            
            is_visible = True if title in DEFAULT_VISIBLE else 'legendonly'

            # 1. Main Data Trace
            fig.add_trace(
                go.Scatter(
                    x=df[X_AXIS_COL], y=df[col_name], name=title, mode='lines', 
                    visible=is_visible, legendgroup=title,
                    line=dict(color=line_color),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                secondary_y=use_secondary, 
            )

            # 2. Add Label Annotation (Top-left corner)
            # This places a small colored indicator in the UI
            fig.add_annotation(
                text=f"● {title}",
                xref="paper", yref="paper",
                x=0.01, y=1.0 - (color_idx * 0.03), # Stack them vertically
                showarrow=False,
                font=dict(size=12, color=line_color),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=line_color,
                borderwidth=1,
                visible=is_visible, # Only shows if the line is on
                name=f"label_{title}" # Metadata for toggling (some Plotly versions)
            )

            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df[X_AXIS_COL].min(), df[X_AXIS_COL].max()], y=[val, val],
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, legendgroup=title, showlegend=False, 
                            visible=is_visible, hoverinfo='skip'
                        ),
                        secondary_y=use_secondary 
                    )
            
            color_idx += 1

    fig.update_layout(
        height=800, 
        template="plotly_white", 
        hovermode="x unified",
        plot_bgcolor="#f8f9fa", 
        paper_bgcolor="white",    
        legend=dict(title="<b>Click to Toggle:</b>", y=0.99, x=1.05),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_xaxes(
        rangeslider_visible=False,
        showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='white'
    )

    fig.update_yaxes(
        showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='white'
    )

    return fig
