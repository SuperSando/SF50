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
    "ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], 
    "N1 %": [(105.7, "red", "Tran. 30sec"), (104.7, "green", "MCT")], 
    "N2 %": [(101, "red", "Tran. 30sec"), (100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df):
    if "Time" in df.columns:
         df["Time"] = pd.to_numeric(df["Time"], errors='coerce')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # High-contrast modern palette
    colors = ['#2E5BFF', '#FF1744', '#00E676', '#D500F9', '#FF9100', '#00B0FF', '#FFEA00', '#1DE9B6']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "") 
            use_secondary = AXIS_MAP.get(unit, False)
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in DEFAULT_VISIBLE else 'legendonly'

            # 1. Main Trace (Slightly thicker for modern feel)
            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], 
                    name=title, 
                    mode='lines', 
                    visible=trace_visible, 
                    legendgroup=title,
                    line=dict(color=line_color, width=2.5),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                secondary_y=use_secondary, 
            )

            # 2. RESTORED: Limit Lines with visible Text Labels
            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], 
                            y=[val, val],
                            mode='lines+text', # Restoration of the labels
                            text=[label, ""], 
                            textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, 
                            legendgroup=title, 
                            showlegend=False, 
                            visible=trace_visible, 
                            hoverinfo='skip'
                        ),
                        secondary_y=use_secondary 
                    )
            color_idx += 1

    fig.update_layout(
        height=800,
        template="plotly_white",
        hovermode="x unified",
        hoverdistance=-1,
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.95)",
            font_size=14,
            font_family="Arial Black",
            font_color="black"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        legend=dict(title="<b>Parameters:</b>", y=0.99, x=1.05),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # RESTORED: Original Axis Titles & Dashed Vertical Strike-Line
    fig.update_xaxes(
        title_text="<b>Time (Seconds)</b>",
        showgrid=True, gridcolor='#F0F2F6',
        showspikes=True, spikemode='across', spikesnap='cursor', 
        spikethickness=2, spikedash='dash', spikecolor='#555555',
        showline=True, linewidth=1, linecolor='black', mirror=True
    )

    fig.update_yaxes(
        title_text="<b>Temp (°F/°C) / Speed (kts)</b>",
        secondary_y=False,
        showgrid=True, gridcolor='#F0F2F6',
        showline=True, linewidth=1, linecolor='black', mirror=True, zeroline=False
    )

    fig.update_yaxes(
        title_text="<b>PSI / % / Degree (°)</b>",
        secondary_y=True,
        showline=True, linewidth=1, linecolor='black', mirror=True, zeroline=False
    )

    return fig
