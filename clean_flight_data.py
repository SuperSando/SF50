import pandas as pd
import os

# --- CONFIGURATION (KEPT FROM ORIGINAL) ---
SKIP_ROWS = 2
KEEP_COL_INDICES = [0, 5, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 83, 86, 89, 98, 101, 107, 110] 
RENAME_MAP = {0: "Time", 5: "Groundspeed", 11: "Cabin Diff PSI", 14: "Bld Px PSI", 17: "Bleed On", 20: "N1 %", 23: "N2 %", 26: "ITT (F)", 29: "Oil Temp (F)", 32: "Oil Px PSI", 35: "TLA DEG", 38: "TT2 (C)", 41: "PT2 PSI", 44: "CHPV", 83: "ECS PRI DUCT T (F)", 86: "ECS PRI DUCT T2 (F)", 89: "ECS CKPT T (F)", 98: "O2 BTL Px PSI", 101: "O2 VLV Open", 107: "EIPS TMP (F)", 110: "EIPS PRS PSI"}
PERCENTAGE_COLUMNS = ["N1 %", "N2 %"]

def clean_data(file_input):
    """Refactored to return a DataFrame for use in other scripts."""
    # 1. Load
    df = pd.read_csv(file_input, header=None, skiprows=SKIP_ROWS)
    
    # 2. Check Columns
    max_idx = max(KEEP_COL_INDICES)
    if max_idx >= len(df.columns):
        raise ValueError(f"File only has {len(df.columns)} columns. Expected at least {max_idx + 1}.")

    # 3. Filter & Rename
    df = df.iloc[:, KEEP_COL_INDICES]
    new_names = [RENAME_MAP[idx] for idx in KEEP_COL_INDICES]
    df.columns = new_names

    # 4. Overwrite Time with Counter
    df['Time'] = range(1, len(df) + 1)
    cols = ['Time'] + [c for c in df.columns if c != 'Time']
    df = df[cols]

    # 5. Convert Percentage
    for col in PERCENTAGE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce') * 100

    return df # Returns the dataframe to the app
