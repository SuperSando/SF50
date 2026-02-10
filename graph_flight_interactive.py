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

# 1 = Top Pane (Performance), 2 = Bottom Pane (Systems)
PANE_MAP = {
    "kts": 1, "°F": 1, "°C": 1, 
    "psi": 2, "%": 2, "°": 2, "1=ON": 2, "1=OPEN": 2, "V": 2 
}

LIMIT_LINES = {
    "ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], 
    "N1 %": [(105.7, "red", "Limit"), (104.7, "green", "MCT")],
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df):
    if "Time" in df.columns:
         df["Time"] = pd.to_numeric(df["Time"], errors='coerce')
    
    # Shared X-axis is key for temporal correlation
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.08,
        subplot_titles=("<b>ENGINE PERFORMANCE & ENVIRONMENT</b>", "<b>SYSTEMS HEALTH & LOGIC</b>")
    )
    
    colors = ['#2E5BFF', '#FF1744', '#00E676', '#D500F9', '#FF9100', '#00B0FF', '#FFEA00', '#1DE9B6']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "") 
            row_idx = PANE_MAP.get(unit, 2)
            
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in DEFAULT_VISIBLE else 'legendonly'

            # Add to the mapped Row
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
                row=row_idx, col=1
            )

            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], 
                            y=[val, val],
                            mode='lines+text', 
                            text=[label, ""], 
                            textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, 
                            legendgroup=title, 
                            showlegend=False, 
                            visible=trace_visible, 
                            hoverinfo='skip'
                        ),
                        row=row_idx, col=1
                    )
            color_idx += 1

    fig.update_layout(
        height=950,
        template="plotly_white",
        hovermode="x unified",
        hoverdistance=-1,
        hoverlabel=dict(bgcolor="rgba(255, 255, 255, 0.95)", font_size=14, font_family="Arial Black", font_color="black"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        legend=dict(title="<b>Parameters:</b>", y=0.5, x=1.05, yanchor="middle"),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # Vertical dash strike-line settings
    spike_style = dict(
        showspikes=True, spikemode='across', spikesnap='cursor', 
        spikethickness=2, spikedash='dash', spikecolor='#555555',
        showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='#F0F2F6'
    )
    
    # Applying spikes to both axes so the line cuts through the entire dashboard
    fig.update_xaxes(spike_style, row=1, col=1)
    fig.update_xaxes(spike_style, row=2, col=1, title_text="<b>Time (Seconds)</b>")

    fig.update_yaxes(title_text="<b>Temp / Speed</b>", row=1, col=1, gridcolor='#F0F2F6', zeroline=False)
    fig.update_yaxes(title_text="<b>PSI / % / Deg</b>", row=2, col=1, gridcolor='#F0F2F6', zeroline=False)

    return fig
