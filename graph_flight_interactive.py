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

AXIS_MAP = {
    "kts": False, "°F": False, "°C": False, 
    "psi": True, "%": True, "°": True, "1=ON": True, "1=OPEN": True, "V": True 
}

LIMIT_LINES = {
    "ITT (F)": [(1610, "#FF0033", "MAX T/O"), (1536, "#00CC66", "MCT")], 
    "N1 %": [(105.7, "#FF0033", "LIMIT"), (104.7, "#00CC66", "MCT")]
}

def generate_dashboard(df):
    if "Time" in df.columns:
         df["Time"] = pd.to_numeric(df["Time"], errors='coerce')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Modern "Cyber" Palette
    colors = ['#2E5BFF', '#FF1744', '#00E676', '#D500F9', '#FF9100', '#00B0FF', '#FFEA00', '#1DE9B6']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "") 
            use_secondary = AXIS_MAP.get(unit, False)
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in DEFAULT_VISIBLE else 'legendonly'

            # 1. Main Trace with Smoothing and Shadow
            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], 
                    name=title, 
                    mode='lines', 
                    visible=trace_visible, 
                    legendgroup=title,
                    line=dict(
                        color=line_color, 
                        width=3, 
                        shape='spline', # Makes the lines smooth/modern
                        smoothing=1.3
                    ),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                secondary_y=use_secondary, 
            )

            # 2. Refined Limit Lines
            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[val, val],
                            mode='lines', 
                            line=dict(color=color, width=1, dash='dot'),
                            name=label, legendgroup=title, showlegend=False, 
                            visible=trace_visible, hoverinfo='skip'
                        ),
                        secondary_y=use_secondary 
                    )
            color_idx += 1

    fig.update_layout(
        height=850,
        template="plotly_white",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.98)",
            font_size=15,
            font_family="Monospace", # Monospace looks more "instrumental"
            font_color="#1A1A1A",
            bordercolor="#D1D1D1"
        ),
        # Pure Light Theme Hardening
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", color="#263238"),
        
        legend=dict(
            title="<b>SYSTEM PARAMETERS</b>",
            y=1, x=1.02,
            bgcolor="rgba(255,255,255,0)",
            bordercolor="#ECEFF1",
            borderwidth=1
        ),
        margin=dict(l=80, r=80, t=50, b=50)
    )

    # Clean, modern axes
    fig.update_xaxes(
        title_text="<b>ELAPSED TIME (SEC)</b>",
        showgrid=True, gridcolor='#F5F5F5',
        showspikes=True, spikemode='across', spikesnap='cursor', 
        spikethickness=1, spikedash='dash', spikecolor='#B0BEC5'
    )

    fig.update_yaxes(
        title_text="<b>ENV / PERFORMANCE</b>",
        secondary_y=False, showgrid=True, gridcolor='#F5F5F5',
        zeroline=False, tickformat=".1f"
    )

    fig.update_yaxes(
        title_text="<b>SYSTEMS / LOGIC</b>",
        secondary_y=True, zeroline=False, tickformat=".1f"
    )

    return fig
