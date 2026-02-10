def generate_dashboard(df, view_mode="Split View", active_list=None):
    if "Time" in df.columns:
        df["Time"] = pd.to_numeric(df["Time"], errors='coerce')

    is_split = "Split View" in view_mode
    if is_split:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    else:
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    for g_name, g_info in GROUPS.items():
        base_color = g_info["color"]
        for i, title in enumerate(g_info["items"]):
            if title in df.columns and (active_list is None or title in active_list):
                val = pd.to_numeric(df[title], errors='coerce')
                unit = UNITS.get(title, "")
                
                # --- COORDINATE MAPPING ---
                # Row 1: Temps/Speed | Row 2: Systems/PSI
                row_idx = 1 if unit in ["kts", "°F", "°C"] else 2
                if not is_split: row_idx = 1
                
                # Secondary Y is ONLY for Single View 'Systems'
                is_sec = False if unit in ["kts", "°F", "°C"] else True

                # 1. ADD DATA TRACE
                fig.add_trace(
                    go.Scatter(
                        x=df["Time"], y=val, name=title, mode='lines',
                        line=dict(color=base_color, width=2, dash=None if i < 3 else 'dot'),
                        legendgroup=g_name,
                        legendgrouptitle_text=g_name if i == 0 else None,
                        hoverlabel=dict(bgcolor="rgba(255,255,255,0.5)", bordercolor=base_color),
                        hovertemplate=f"<b>{title}</b>: %{{y:.1f}} {unit}<extra></extra>"
                    ),
                    row=row_idx, col=1,
                    secondary_y=is_sec if not is_split else None
                )

                # 2. ADD LIMIT LINES (Locked to the same Row/Axis as the trace)
                if title in LIMIT_LINES:
                    for l_val, l_color, l_label in LIMIT_LINES[title]:
                        fig.add_trace(
                            go.Scatter(
                                x=[df["Time"].min(), df["Time"].max()], 
                                y=[l_val, l_val],
                                mode='lines+text', 
                                text=[f" {l_label}", ""], 
                                textposition="top right",
                                line=dict(color=l_color, width=1, dash='dash'),
                                hoverinfo='skip', 
                                showlegend=False, 
                                legendgroup=g_name,
                                visible=True # Ensures they toggle with the parent trace
                            ),
                            row=row_idx, col=1, # FORCES limit to same row as data
                            secondary_y=is_sec if not is_split else None # FORCES limit to same Y-scale
                        )

    # ... (Rest of layout/spikes logic remains the same)
    return fig
