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

LIMIT_LINES = {
    "ITT (F)": [(1610, "red", "Max T/O 10sec"), (1583, "orange", "Max T/O 5mins"), (1536, "green", "MCT")], 
    "N1 %": [(105.7, "red", "Tran. 30sec"), (104.7, "green", "MCT")], 
    "N2 %": [(101, "red", "Tran. 30sec"), (100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df, view_mode="Single View"):
    if "Time" in df.columns:
        df["Time"] = pd.to_numeric(df["Time"], errors='coerce')

    is_split = "Split View" in view_mode
    
    # Initialize Subplots
    if is_split:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03)
        height = 850
    else:
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
        height = 800

    colors = ['#2E5BFF', '#FF1744', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            unit = UNITS.get(title, "")
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in ["ITT (F)", "N1 %", "Groundspeed"] else 'legendonly'

            row = 1 if unit in ["kts", "°F", "°C"] else (2 if is_split else 1)
            is_sec = False if unit in ["kts", "°F", "°C"] else True

            # DATA TRACES
            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], name=title, mode='lines',
                    line=dict(color=line_color, width=2.5),
                    visible=trace_visible,
                    # TRANSLUCENT HOVER LABELS
                    hoverlabel=dict(
                        bgcolor="rgba(255,255,255,0.6)", # High translucency
                        bordercolor=line_color,
                        font=dict(family="Arial Black", size=12, color="black")
                    ),
                    hovertemplate=f"<b>{title}</b><br>%{{y:.1f}} {unit}<extra></extra>"
                ),
                row=row, col=1,
                secondary_y=is_sec if not is_split else None
            )

            # LIMIT LINES (Restored with Labels)
            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[val, val],
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            hoverinfo='skip', showlegend=False, visible=trace_visible
                        ),
                        row=row, col=1
                    )
            color_idx += 1

    # --- THE MAGIC SETTINGS FOR SYNCHRONIZATION ---
    fig.update_layout(
        height=height,
        template="plotly_white",
        hovermode="x", # Forces all traces on the X-axis to report
        hoverdistance=-1,
        spikedistance=-1,
        margin=dict(l=20, r=20, t=30, b=50),
        legend=dict(y=0.5, x=1.05)
    )

    # Spike Configuration
    spike_style = dict(
        showspikes=True,
        spikemode='across', # Draws the line across the entire plot height
        spikesnap='cursor',
        spikethickness=2,
        spikedash='dash',
        spikecolor='#555555',
        showline=True, linewidth=1, linecolor='black', mirror=True
    )

    if is_split:
        # Match X-axes so interactions on one trigger the other
        fig.update_xaxes(spike_style, row=1, col=1, matches='x')
        fig.update_xaxes(spike_style, row=2, col=1, title_text="<b>Time (Seconds)</b>", matches='x')
        fig.update_yaxes(title_text="<b>Perf / Speed</b>", row=1, col=1, showline=True, linecolor='black')
        fig.update_yaxes(title_text="<b>Systems / PSI</b>", row=2, col=1, showline=True, linecolor='black')
    else:
        fig.update_xaxes(spike_style, title_text="<b>Time (Seconds)</b>")
        fig.update_yaxes(title_text="<b>Perf / Speed</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>Systems / PSI</b>", secondary_y=True)

    return fig
