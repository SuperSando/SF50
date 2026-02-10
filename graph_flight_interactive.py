import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. SYSTEM HIERARCHY ---
GROUPS = {
    "Powerplant": {"color": "#D32F2F", "items": ["N1 %", "N2 %", "ITT (F)", "Oil Temp (F)", "Oil Px PSI", "TLA DEG"]},
    "Environmental": {"color": "#1976D2", "items": ["Cabin Diff PSI", "Bld Px PSI", "Bleed On", "ECS PRI DUCT T (F)", "ECS PRI DUCT T2 (F)", "ECS CKPT T (F)"]},
    "Airframe/Ice": {"color": "#388E3C", "items": ["EIPS TMP (F)", "EIPS PRS PSI", "TT2 (C)", "PT2 PSI"]},
    "Avionics/O2": {"color": "#7B1FA2", "items": ["O2 BTL Px PSI", "O2 VLV Open", "CHPV", "Groundspeed"]}
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
    "ITT (F)": [(1610, "red", "Max T/O"), (1536, "green", "MCT")], 
    "N1 %": [(104.7, "green", "MCT")], 
    "N2 %": [(100, "green", "MCT")], 
    "Oil Px PSI": [(120, "green", "max")]
}

def generate_dashboard(df_input, view_mode="Split View", active_list=None):
    df = df_input.copy()
    if "Time" in df.columns:
        df["Time"] = pd.to_numeric(df["Time"], errors='coerce')
    else:
        df["Time"] = range(len(df))

    is_split = "Split View" in view_mode
    
    # FIX: Initialize with specific specs to prevent axis 'ghosting'
    if is_split:
        # Two rows, each with their own independent Y-axis
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07)
    else:
        # Single row with a secondary Y-axis
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    for g_name, g_info in GROUPS.items():
        base_color = g_info["color"]
        for i, title in enumerate(g_info["items"]):
            if title in df.columns and (active_list is None or title in active_list):
                val = pd.to_numeric(df[title], errors='coerce')
                unit = UNITS.get(title, "")
                
                # Assign Row/Axis based on Unit
                is_engine = unit in ["kts", "°F", "°C"]
                
                # Placement Logic
                curr_row = 1 if (is_engine or not is_split) else 2
                use_sec_y = (not is_engine) if not is_split else False

                # 1. TRACE
                fig.add_trace(
                    go.Scatter(
                        x=df["Time"], y=val, name=title, mode='lines',
                        line=dict(color=base_color, width=2, dash=None if i < 3 else 'dot'),
                        legendgroup=g_name,
                        legendgrouptitle_text=g_name if i == 0 else None,
                        hoverlabel=dict(bgcolor="rgba(255,255,255,0.5)", bordercolor=base_color),
                        hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                    ),
                    row=curr_row, col=1, secondary_y=use_sec_y
                )

                # 2. LIMITS - Anchored strictly to the same row and axis as the data
                if title in LIMIT_LINES:
                    for l_val, l_color, l_label in LIMIT_LINES[title]:
                        fig.add_trace(
                            go.Scatter(
                                x=[df["Time"].min(), df["Time"].max()], y=[l_val, l_val],
                                mode='lines+text', text=[f" {l_label}", ""], textposition="top right",
                                line=dict(color=l_color, width=1.5, dash='dash'),
                                hoverinfo='skip', showlegend=False, legendgroup=g_name
                            ),
                            row=curr_row, col=1, secondary_y=use_sec_y
                        )

    # Global Layout tweaks to fix the 'missing plot' issue
    fig.update_layout(
        height=850,
        template="plotly_white",
        hovermode="x",
        margin=dict(l=60, r=60, t=30, b=50),
        legend=dict(groupclick="toggleitem", y=0.5, x=1.1),
        xaxis=dict(showspikes=True, spikemode='across', spikesnap='cursor',
                   spikethickness=2, spikedash='dash', spikecolor='black')
    )

    if is_split:
        # Label Row 1
        fig.update_yaxes(title_text="<b>Performance / Engine</b>", row=1, col=1, showgrid=True)
        # Label Row 2
        fig.update_yaxes(title_text="<b>Systems / Air</b>", row=2, col=1, showgrid=True)
        # Ensure X-axis is only at the bottom
        fig.update_xaxes(title_text="Time (Seconds)", row=2, col=1)
    else:
        fig.update_yaxes(title_text="<b>Performance / Engine</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>Systems / Air</b>", secondary_y=True)
        fig.update_xaxes(title_text="Time (Seconds)")

    return fig
