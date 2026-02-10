import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIG (Same as before) ---
GRAPH_MAPPINGS = { ... } # Your mappings
UNITS = { ... } # Your units
LIMIT_LINES = { ... } # Your limits
PANE_MAP = { "kts": 1, "°F": 1, "°C": 1, "psi": 2, "%": 2, "°": 2, "1=ON": 2, "1=OPEN": 2, "V": 2 }

def generate_dashboard(df, view_mode="Single View"):
    if "Time" in df.columns:
         df["Time"] = pd.to_numeric(df["Time"], errors='coerce')

    # --- DYNAMIC SUBPLOT INITIALIZATION ---
    if "Split View" in view_mode:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08,
            subplot_titles=("<b>PERFORMANCE & ENVIRONMENT</b>", "<b>SYSTEMS HEALTH & LOGIC</b>")
        )
        height = 950
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        height = 800

    colors = ['#2E5BFF', '#FF1744', '#00E676', '#D500F9', '#FF9100', '#00B0FF', '#FFEA00', '#1DE9B6']
    color_idx = 0

    for title, col_name in GRAPH_MAPPINGS.items():
        if col_name in df.columns:
            unit = UNITS.get(title, "") 
            line_color = colors[color_idx % len(colors)]
            trace_visible = True if title in ["ITT (F)", "N1 %", "Groundspeed"] else 'legendonly'

            # Logic for Row and Axis
            if "Split View" in view_mode:
                row_idx, col_idx, sec_y = PANE_MAP.get(unit, 2), 1, False
            else:
                row_idx, col_idx, sec_y = 1, 1, (unit in ["psi", "%", "°", "1=ON", "1=OPEN", "V"])

            # Add Main Trace
            fig.add_trace(
                go.Scatter(
                    x=df["Time"], y=df[col_name], name=title, mode='lines', 
                    visible=trace_visible, legendgroup=title,
                    line=dict(color=line_color, width=2.5),
                    hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                ),
                row=row_idx, col=col_idx, secondary_y=sec_y if "Split" not in view_mode else None
            )

            # Add Limit Lines
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
                        row=row_idx, col=col_idx, secondary_y=sec_y if "Split" not in view_mode else None
                    )
            color_idx += 1

    # --- SHARED STYLING ---
    fig.update_layout(
        height=height, template="plotly_white", hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial Black", font_color="black"),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"),
        legend=dict(title="<b>Parameters:</b>", y=0.5, x=1.05, yanchor="middle"),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    spike_style = dict(
        showspikes=True, spikemode='across', spikesnap='cursor', 
        spikethickness=2, spikedash='dash', spikecolor='#555555',
        showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='#F0F2F6'
    )

    if "Split View" in view_mode:
        fig.update_xaxes(spike_style, row=1, col=1)
        fig.update_xaxes(spike_style, row=2, col=1, title_text="<b>Time (Seconds)</b>")
        fig.update_yaxes(title_text="<b>Temp / Speed</b>", row=1, col=1, gridcolor='#F0F2F6', zeroline=False)
        fig.update_yaxes(title_text="<b>PSI / % / Deg</b>", row=2, col=1, gridcolor='#F0F2F6', zeroline=False)
    else:
        fig.update_xaxes(spike_style, title_text="<b>Time (Seconds)</b>")
        fig.update_yaxes(title_text="<b>Temp / Speed</b>", secondary_y=False, gridcolor='#F0F2F6', zeroline=False)
        fig.update_yaxes(title_text="<b>PSI / % / Deg</b>", secondary_y=True, zeroline=False)

    return fig
