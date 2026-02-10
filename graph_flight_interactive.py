import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. CONFIGURATION ---
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

UNITS = {
    "Groundspeed": "kts", "Cabin Diff PSI": "psi", "Bld Px PSI": "psi", 
    "Bleed On": "1=ON", "N1 %": "%", "N2 %": "%", "ITT (F)": "°F", 
    "Oil Temp (F)": "°F", "Oil Px PSI": "psi", "TLA DEG": "°", "TT2 (C)": "°C", 
    "PT2 PSI": "psi", "CHPV": "V", "ECS PRI DUCT T (F)": "°F", 
    "ECS PRI DUCT T2 (F)": "°F", "ECS CKPT T (F)": "°F", 
    "O2 BTL Px PSI": "psi", "O2 VLV Open": "1=OPEN", "EIPS TMP (F)": "°F", 
    "EIPS PRS PSI": "psi"
}

PANE_MAP = {
    "kts": 1, "°F": 1, "°C": 1, 
    "psi": 2, "%": 2, "°": 2, "1=ON": 2, "1=OPEN": 2, "V": 2 
}

LIMIT_LINES = {
    "ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], 
    "N1 %": [(105.7, "red", "Tran. 30sec"), (104.7, "green", "MCT")], 
    "N2 %": [(101, "red", "Tran. 30sec"), (100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df, view_mode="Single View"):
    if "Time" in df.columns:
         df["Time"] = pd.to_numeric(df["Time"], errors='coerce')

    if "Split View" in view_mode:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.02, # Very tight to make the line look continuous
        )
        height = 950
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        height = 800

    colors = ['#2E5BFF', '#FF1744', '#00E676', '#D500F9', '#FF9100', '#00B0FF', '#FFEA00', '#1DE9B6']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "") 
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in ["ITT (F)", "N1 %", "Groundspeed"] else 'legendonly'

            if "Split View" in view_mode:
                row_idx, sec_y = PANE_MAP.get(unit, 2), False
            else:
                row_idx, sec_y = 1, (unit in ["psi", "%", "°", "1=ON", "1=OPEN", "V"])

            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], name=title, mode='lines', 
                    visible=trace_visible, legendgroup=title,
                    line=dict(color=line_color, width=2.5),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                row=row_idx, col=1, secondary_y=sec_y if "Split" not in view_mode else None
            )

            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[val, val],
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, legendgroup=title, showlegend=False, 
                            visible=trace_visible, hoverinfo='skip'
                        ),
                        row=row_idx, col=1, secondary_y=sec_y if "Split" not in view_mode else None
                    )
            color_idx += 1

    fig.update_layout(
        height=height, 
        template="plotly_white", 
        hovermode="x unified",
        hoverdistance=-1, # Ensure hover triggers across both subplots
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial Black", font_color="black"),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"),
        legend=dict(title="<b>Parameters:</b>", y=0.5, x=1.05, yanchor="middle"),
        margin=dict(l=20, r=20, t=20, b=20)
    )

    # --- THE MAGIC FOR THE CONTINUOUS LINE ---
    spike_style = dict(
        showspikes=True, 
        spikemode='across', 
        spikesnap='cursor', 
        spikethickness=2, 
        spikedash='dash', 
        spikecolor='#555555',
        showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='#F0F2F6'
    )

    if "Split View" in view_mode:
        # Force Row 2 to match Row 1's X-axis and enable spikes on both
        fig.update_xaxes(spike_style, row=1, col=1)
        fig.update_xaxes(spike_style, row=2, col=1, title_text="<b>Time (Seconds)</b>", matches='x')
        
        fig.update_yaxes(title_text="<b>Temp / Speed</b>", row=1, col=1, gridcolor='#F0F2F6', zeroline=False)
        fig.update_yaxes(title_text="<b>PSI / % / Deg</b>", row=2, col=1, gridcolor='#F0F2F6', zeroline=False)
    else:
        fig.update_xaxes(spike_style, title_text="<b>Time (Seconds)</b>")
        fig.update_yaxes(title_text="<b>Temp / Speed</b>", secondary_y=False, gridcolor='#F0F2F6', zeroline=False)
        fig.update_yaxes(title_text="<b>PSI / % / Deg</b>", secondary_y=True, zeroline=False)

    return fig
