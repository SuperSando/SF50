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

PANE_MAP = {
    "kts": "y1", "°F": "y1", "°C": "y1", 
    "psi": "y2", "%": "y2", "°": "y2", "1=ON": "y2", "1=OPEN": "y2", "V": "y2" 
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
    colors = ['#2E5BFF', '#FF1744', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            unit = UNITS.get(title, "") 
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in ["ITT (F)", "N1 %", "Groundspeed"] else 'legendonly'

            # Logic for "Single" vs "Split" View
            if "Split View" in view_mode:
                target_yaxis = PANE_MAP.get(unit, "y2")
            else:
                target_yaxis = "y1" if unit in ["kts", "°F", "°C"] else "y2"

            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], name=title, mode='lines', 
                    visible=trace_visible, legendgroup=title,
                    yaxis="y2" if target_yaxis == "y2" else "y",
                    line=dict(color=line_color, width=2.5),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                )
            )

            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df["Time"].min(), df["Time"].max()], y=[val, val],
                            yaxis="y2" if target_yaxis == "y2" else "y",
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, legendgroup=title, showlegend=False, 
                            visible=trace_visible, hoverinfo='skip'
                        )
                    )
            color_idx += 1

    is_split = "Split View" in view_mode
    
    layout_config = dict(
        height=800, # FIXED: Reduced height
        template="plotly_white", 
        hovermode="x unified",
        hoverdistance=-1,
        spikedistance=-1,
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial Black", font_color="black"),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"),
        legend=dict(title="<b>Parameters:</b>", y=0.5, x=1.05, yanchor="middle"),
        margin=dict(l=20, r=20, t=30, b=50),
        
        xaxis=dict(
            title_text="<b>Time (Seconds)</b>",
            anchor="y2" if is_split else "y",
            showgrid=True, gridcolor='#F0F2F6',
            showspikes=True, spikemode='across', spikesnap='cursor',
            spikethickness=2, spikedash='dash', spikecolor='#555555',
            showline=True, linewidth=1, linecolor='black', mirror=True # Mirror adds the top line back
        ),
        
        yaxis=dict(
            title_text="<b>Temp / Speed</b>",
            domain=[0.52, 1] if is_split else [0, 1],
            gridcolor='#F0F2F6', zeroline=False, showline=True, linecolor='black', mirror=True
        )
    )

    if is_split:
        layout_config["yaxis2"] = dict(
            title_text="<b>PSI / % / Deg</b>",
            domain=[0, 0.48], # Tighter vertical gap
            gridcolor='#F0F2F6', zeroline=False, showline=True, linecolor='black', mirror=True
        )
    else:
        layout_config["yaxis2"] = dict(
            title_text="<b>PSI / % / Deg</b>",
            overlaying="y",
            side="right",
            zeroline=False, showline=True, linecolor='black'
        )

    fig.update_layout(layout_config)
    return fig
