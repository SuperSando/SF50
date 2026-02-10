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
    "ITT (F)": [(1610, "red", "Max T/O"), (1583, "orange", "Max T/O 5min"), (1536, "green", "MCT")], 
    "N1 %": [(104.7, "green", "MCT")], 
    "N2 %": [(100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df_input, view_mode="Split View"):
    df = df_input.copy()
    if "Time" in df.columns:
        df["Time"] = pd.to_numeric(df["Time"], errors='coerce')

    is_split = "Split View" in view_mode
    
    # Initialize Subplots
    if is_split:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
    else:
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    # 20 Distinct Colors
    colors = ['#2E5BFF', '#FF1744', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52', 
              '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, (title, col_name) in enumerate(GRAPH_MAPPINGS.items()):
        if col_name in df.columns:
            data = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "")
            line_color = colors[i % len(colors)]
            
            # Default visibility
            is_visible = True if title in ["N2 %", "Bld Px PSI"] else 'legendonly'

            # Logic: Row 1 = Speeds/Temps | Row 2 = PSI/%/Systems
            is_perf_group = unit in ["kts", "°F", "°C"]
            target_row = 1 if (is_perf_group or not is_split) else 2
            target_sec_y = (not is_perf_group) if not is_split else False

            # 1. ADD DATA TRACE
            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=data, name=title, mode='lines',
                    line=dict(color=line_color, width=2.5),
                    visible=is_visible,
                    legendgroup=title, # LOCK TO TITLE
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                row=target_row, col=1, secondary_y=target_sec_y
            )

            # 2. ADD LIMIT LINES (Linked to Title and Visibility)
            if title in LIMIT_LINES:
                for l_val, l_color, l_label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[l_val, l_val],
                            mode='lines+text', 
                            text=[f" {l_label}", ""], 
                            textposition="top right",
                            line=dict(color=l_color, width=1.2, dash='dash'),
                            hoverinfo='skip', 
                            showlegend=False, 
                            visible=is_visible, # SYNCED
                            legendgroup=title   # SYNCED
                        ),
                        row=target_row, col=1, secondary_y=target_sec_y
                    )

    fig.update_layout(
        height=850,
        template="plotly_white",
        hovermode="x",
        margin=dict(l=60, r=60, t=30, b=50),
        legend=dict(y=0.5, x=1.05, font=dict(size=10))
    )

    common_x = dict(
        showspikes=True, spikemode='across', spikesnap='cursor',
        spikethickness=2, spikedash='dash', spikecolor='#444',
        showline=True, linecolor='black', mirror=True
    )

    if is_split:
        fig.update_xaxes(common_x, row=1, col=1, matches='x')
        fig.update_xaxes(common_x, row=2, col=1, title_text="Time (Seconds)", matches='x')
        fig.update_yaxes(title_text="<b>Performance / Temp</b>", row=1, col=1)
        fig.update_yaxes(title_text="<b>Systems / PSI / %</b>", row=2, col=1)
    else:
        fig.update_xaxes(common_x, title_text="Time (Seconds)")
        fig.update_yaxes(title_text="<b>Performance / Temp</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>Systems / PSI / %</b>", secondary_y=True)

    return fig
