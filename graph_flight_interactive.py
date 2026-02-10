import pandas as pd
import plotly.graph_objects as go

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

    fig = go.Figure()
    is_split = "Split View" in view_mode
    colors = ['#2E5BFF', '#FF1744', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            unit = UNITS.get(title, "")
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in ["ITT (F)", "N1 %", "Groundspeed"] else 'legendonly'

            # Define which Y-axis to use. 
            # In Split: Performance -> y1, Systems -> y2.
            # In Single: Temp/Speed -> y1, Others -> y2 (Right side).
            if is_split:
                target_yaxis = "y2" if unit in ["psi", "%", "°", "1=ON", "1=OPEN", "V"] else "y"
            else:
                target_yaxis = "y" if unit in ["kts", "°F", "°C"] else "y2"

            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], name=title, mode='lines',
                    line=dict(color=line_color, width=2),
                    visible=trace_visible,
                    yaxis=target_yaxis.replace("y", "y") if target_yaxis != "y" else "y",
                    hoverlabel=dict(
                        bgcolor="rgba(255, 255, 255, 0.5)", # 50% Translucent
                        bordercolor=line_color,
                        font=dict(family="Arial Black", size=11, color="black")
                    ),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                )
            )

            # Limit Lines Restored with Text
            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[val, val],
                            yaxis=target_yaxis.replace("y", "y") if target_yaxis != "y" else "y",
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            hoverinfo='skip', showlegend=False, visible=trace_visible
                        )
                    )
            color_idx += 1

    # --- LAYOUT LOGIC ---
    layout_cfg = dict(
        height=800,
        template="plotly_white",
        hovermode="x", # Shows ALL trace boxes on the X-line
        margin=dict(l=60, r=60, t=30, b=50),
        
        xaxis=dict(
            title="Time (Seconds)",
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikethickness=1, spikedash='dash', spikecolor='black',
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        
        yaxis=dict(
            title="Performance",
            domain=[0.53, 1] if is_split else [0, 1],
            showline=True, linecolor='black', mirror=True, zeroline=False
        ),
        
        yaxis2=dict(
            title="Systems",
            domain=[0, 0.47] if is_split else [0, 1],
            overlaying="y" if not is_split else None,
            side="right" if not is_split else "left",
            showline=True, linecolor='black', mirror=True, zeroline=False
        )
    )

    if is_split:
        # Static Divider Shape
        layout_cfg["shapes"] = [
            dict(type="line", xref="paper", yref="paper", x0=0, x1=1, y0=0.5, y1=0.5,
                 line=dict(color="black", width=1))
        ]

    fig.update_layout(layout_cfg)
    return fig
