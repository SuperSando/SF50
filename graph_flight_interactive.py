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

    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color_idx = 0

    left_axis_labels = []
    right_axis_labels = []

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            max_val = df[col_name].max()
            use_secondary = not (max_val > BIG_NUMBER_THRESHOLD)
            unit = UNITS.get(title, "") 
            line_color = colors[color_idx % len(colors)]
            
            trace_visible = True if title in DEFAULT_VISIBLE else 'legendonly'

            if trace_visible is True:
                if use_secondary: right_axis_labels.append(unit)
                else: left_axis_labels.append(unit)

            fig.add_trace(
                go.Scatter(
                    x=df[X_AXIS_COL], y=df[col_name], name=title, mode='lines', 
                    visible=trace_visible, legendgroup=title,
                    line=dict(color=line_color, width=2),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                secondary_y=use_secondary, 
            )

            if title in LIMIT_LINES:
                for val, color, label in LIMIT_LINES[title]:
                    fig.add_trace(
                        go.Scatter(
                            x=[df[X_AXIS_COL].min(), df[X_AXIS_COL].max()], y=[val, val],
                            mode='lines+text', text=[label, ""], textposition="top right",
                            line=dict(color=color, width=1, dash='dash'),
                            name=label, legendgroup=title, showlegend=False, 
                            visible=trace_visible, hoverinfo='skip'
                        ),
                        secondary_y=use_secondary 
                    )
            
            color_idx += 1

    left_title = " / ".join(sorted(list(set(left_axis_labels)))) if left_axis_labels else "Primary Value"
    right_title = " / ".join(sorted(list(set(right_axis_labels)))) if right_axis_labels else "Secondary Value"

    fig.update_layout(
        height=800, 
        template="plotly_white", # Hardcoded light template
        hovermode="x unified",
        hoverdistance=-1, 
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial Black", font_color="black"),
        plot_bgcolor="white",    # Ensures white background inside plot
        paper_bgcolor="white",   # Ensures white background around plot
        font=dict(color="black"), # Forces text to black
        legend=dict(title="<b>Click to Toggle:</b>", y=0.99, x=1.05, font=dict(color="black")),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_xaxes(
        title_text="Time (Seconds)",
        title_font=dict(color="black"),
        tickfont=dict(color="black"),
        showspikes=True, spikemode='across', spikesnap='cursor', 
        spikethickness=2, spikedash='dash', spikecolor='#555555',
        rangeslider_visible=False, showline=True, linewidth=1, 
        linecolor='black', mirror=True, gridcolor='#F0F2F6'
    )

    fig.update_yaxes(
        title_text=f"<b>{left_title}</b>",
        title_font=dict(color="black"),
        tickfont=dict(color="black"),
        secondary_y=False,
        showgrid=True, gridcolor='#F0F2F6', gridwidth=1,
        showline=True, linewidth=1, linecolor='black', mirror=True, zeroline=False
    )

    fig.update_yaxes(
        title_text=f"<b>{right_title}</b>",
        title_font=dict(color="black"),
        tickfont=dict(color="black"),
        secondary_y=True,
        showline=True, linewidth=1, linecolor='black', mirror=True, zeroline=False
    )

    return fig
