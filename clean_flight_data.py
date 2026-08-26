import pandas as pd
import numpy as np
import os

# ==========================================
# --- OLD FORMAT CONFIGURATION (STANDARD CSV) ---
# ==========================================
OLD_SKIP_ROWS = 0
OLD_INDICES = [0, 5, 8, 13, 14, 15] 
OLD_RENAME_MAP = {
    0: "Time", 5: "Altitude", 8: "Airspeed", 
    13: "RPM", 14: "Throttle_Pos", 15: "Fuel_Level"
}
OLD_PERCENTAGE_COLS = ["Throttle_Pos", "Fuel_Level"]

# ==========================================
# --- NEW FORMAT CONFIGURATION (SF50 TELEMETRY) ---
# ==========================================
NEW_SKIP_ROWS = 2
# Corrected indices based on the raw file structure
NEW_INDICES = [0, 5, 11, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 89, 92, 95, 104, 107, 113, 116] 

NEW_RENAME_MAP = {
    0: "Time", 
    5: "Groundspeed", 
    11: "Cabin Diff PSI", 
    20: "Bld Px PSI",        
    23: "Bleed On",          
    26: "N1 %",              
    29: "N2 %",              
    32: "ITT (F)",           
    35: "Oil Temp (F)",      
    38: "Oil Px PSI",        
    41: "TLA DEG",           
    44: "TT2 (C)",           
    47: "PT2 PSI",           
    50: "CHPV",              
    89: "ECS PRI DUCT T (F)",
    92: "ECS PRI DUCT T2 (F)",
    95: "ECS CKPT T (F)",    
    104: "O2 BTL Px PSI",    
    107: "O2 VLV Open",      
    113: "EIPS TMP (F)",     
    116: "EIPS PRS PSI"      
}
NEW_PERCENTAGE_COLS = ["N1 %", "N2 %"]

# ==========================================
# --- ANOMALY REPLACEMENT ---
# ==========================================
ANOMALY_FIXES = [
    (9.89999976239994E+24, 9.8) 
]

def clean_data(file_input):
    """Auto-detects format, cleans anomalies, and returns a DataFrame."""
    
    # 1. Auto-Detect Format
    file_content = file_input.getvalue().decode("utf-8", errors="replace")
    top_lines = file_content.splitlines()[:5]
    
    # Check if it's the newer SF50 telemetry log
    is_sf50 = any("Cirrus SF50" in line or "Alert Name" in line for line in top_lines)
    
    if is_sf50:
        skip_rows = NEW_SKIP_ROWS
        indices = NEW_INDICES
        rename_map = NEW_RENAME_MAP
        pct_cols = NEW_PERCENTAGE_COLS
    else:
        skip_rows = OLD_SKIP_ROWS
        indices = OLD_INDICES
        rename_map = OLD_RENAME_MAP
        pct_cols = OLD_PERCENTAGE_COLS

    # 2. Load Data
    file_input.seek(0) # Reset file pointer for Pandas
    df = pd.read_csv(file_input, header=None, skiprows=skip_rows)
    
    # 3. Check Columns
    max_idx = max(indices)
    if max_idx >= len(df.columns):
        raise ValueError(f"File only has {len(df.columns)} columns. Expected at least {max_idx + 1}.")

    # 4. Filter & Rename
    df = df.iloc[:, indices]
    new_names = [rename_map[idx] for idx in indices]
    df.columns = new_names

    # 5. Anomaly Fixing
    for col in df.columns:
        if col == "Time": continue
        
        df[col] = pd.to_numeric(df[col], errors='coerce')
        for bad_val, new_val in ANOMALY_FIXES:
            mask = np.isclose(df[col], bad_val, atol=1e15) 
            if mask.any():
                df.loc[mask, col] = new_val

    # 6. Overwrite Time with Counter
    df['Time'] = range(1, len(df) + 1)
    cols = ['Time'] + [c for c in df.columns if c != 'Time']
    df = df[cols]

    # 7. Convert Percentage
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col] * 100

    return df, is_sf50
