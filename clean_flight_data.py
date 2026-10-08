import io
import csv
import pandas as pd
import numpy as np

def clean_data(file_input):
    """
    Auto-detects and normalizes SF50 flight logs.
    Returns: (df_clean, is_sf50)
    """
    # 1. Read raw text safely from Streamlit UploadedFile or file path
    if hasattr(file_input, "getvalue"):
        raw_bytes = file_input.getvalue()
        raw_text = raw_bytes.decode("utf-8", errors="replace")
    elif hasattr(file_input, "read"):
        raw_text = file_input.read()
        if isinstance(raw_text, bytes):
            raw_text = raw_text.decode("utf-8", errors="replace")
    else:
        with open(file_input, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

    reader = list(csv.reader(io.StringIO(raw_text)))
    if not reader or len(reader) < 2:
        return pd.DataFrame(), False

    # Check for SF50 airframe signature in file header or metadata
    header_chunk = " ".join(" ".join(row) for row in reader[:3]).upper()
    is_sf50 = ("CIRRUS SF50" in header_chunk) or ("SF50" in header_chunk)

    # 2. Identify file format
    # Format A: Garmin MFD Alert/Trigger log (repeated "Trigger Name", "Trigger Value")
    if len(reader) >= 3 and "Trigger Name" in reader[1]:
        df_clean = _parse_trigger_format(reader)
        # If trigger format contains Vision Jet systems (e.g. ITT, CAB DIF, EIPS), treat as SF50
        if not is_sf50 and "N1" in reader[2] and "ITT" in reader[2]:
            is_sf50 = True
        return df_clean, is_sf50
    else:
        # Format B: Standard columnar CSV
        df_clean = _parse_standard_format(io.StringIO(raw_text))
        return df_clean, is_sf50


def _parse_trigger_format(rows):
    header_row = rows[1]
    name_row = rows[2]

    # Map parameter names to their Trigger Value column index
    col_map = {}
    for i in range(len(header_row)):
        if header_row[i].strip() == "Trigger Name" and i + 1 < len(header_row):
            param_name = name_row[i].strip()
            val_col_idx = i + 1
            col_map[param_name] = val_col_idx

    data_rows = rows[2:]

    # Parse timestamps into elapsed seconds
    ts_list = [r[0].strip() for r in data_rows]
    try:
        ts_series = pd.to_datetime(ts_list)
        time_sec = (ts_series - ts_series[0]).total_seconds().values
    except Exception:
        time_sec = np.arange(len(data_rows))

    df_out = pd.DataFrame({"Time": time_sec})

    def get_series(param_name):
        if param_name not in col_map:
            return pd.Series([np.nan] * len(data_rows))
        idx = col_map[param_name]
        vals = [r[idx] if idx < len(r) else np.nan for r in data_rows]
        s = pd.to_numeric(pd.Series(vals), errors="coerce")
        # Filter uninitialized float glitches (e.g. 9.89e+24)
        s[s > 1e6] = np.nan
        return s

    # Canonical parameter mappings
    df_out["Groundspeed"] = get_series("GROUNDSPEED > 30KTS")
    df_out["Cabin Diff PSI"] = get_series("CAB DIF")
    df_out["Bld Px PSI"] = get_series("BLD PRS")
    df_out["Bleed On"] = get_series("BLD ON")

    # Scale fractional rotor speeds (0.0 to 1.0) -> %
    raw_n1 = get_series("N1")
    df_out["N1 %"] = raw_n1 * 100.0 if raw_n1.dropna().max() <= 1.5 else raw_n1

    raw_n2 = get_series("N2")
    df_out["N2 %"] = raw_n2 * 100.0 if raw_n2.dropna().max() <= 1.5 else raw_n2

    df_out["ITT (F)"] = get_series("ITT")
    df_out["Oil Temp (F)"] = get_series("OIL TMP")
    df_out["Oil Px PSI"] = get_series("OIL PRS")
    df_out["TLA DEG"] = get_series("TLA")
    df_out["TT2 (C)"] = get_series("TT2")
    df_out["PT2 PSI"] = get_series("PT2")
    df_out["CHPV"] = get_series("CHPV")
    df_out["ECS PRI DUCT T (F)"] = get_series("ECS PRI DUCT T")
    df_out["ECS PRI DUCT T2 (F)"] = get_series("ECS PRI DUCT T2")
    df_out["ECS CKPT T (F)"] = get_series("ECS CKPT T")
    df_out["O2 BTL Px PSI"] = get_series("O2 BTL PRESS")
    df_out["O2 VLV Open"] = get_series("O2 VLV OPEN")
    df_out["EIPS TMP (F)"] = get_series("EIPS TMP")
    df_out["EIPS PRS PSI"] = get_series("EIPS PRS")

    return df_out


def _parse_standard_format(stream):
    df_raw = pd.read_csv(stream)
    df_raw.columns = [c.strip() for c in df_raw.columns]

    df_out = pd.DataFrame()

    time_col = next((c for c in df_raw.columns if c.lower() in ["time", "time (sec)", "seconds"]), None)
    if time_col:
        df_out["Time"] = pd.to_numeric(df_raw[time_col], errors="coerce")
    else:
        df_out["Time"] = np.arange(len(df_raw))

    mappings = {
        "Groundspeed": ["Groundspeed", "GndSpd", "GPS Ground Speed"],
        "Cabin Diff PSI": ["Cabin Diff PSI", "CAB DIF", "CabDiff"],
        "Bld Px PSI": ["Bld Px PSI", "BLD PRS", "Bleed Pres"],
        "Bleed On": ["Bleed On", "BLD ON"],
        "N1 %": ["N1 %", "N1%", "E1 N1 %", "ENG N1 %", "N1"],
        "N2 %": ["N2 %", "N2%", "E1 N2 %", "ENG N2 %", "N2"],
        "ITT (F)": ["ITT (F)", "ITT", "E1 ITT", "ENG ITT"],
        "Oil Temp (F)": ["Oil Temp (F)", "OIL TMP", "E1 Oil Temp"],
        "Oil Px PSI": ["Oil Px PSI", "OIL PRS", "E1 Oil Pres"],
        "TLA DEG": ["TLA DEG", "TLA"],
        "TT2 (C)": ["TT2 (C)", "TT2"],
        "PT2 PSI": ["PT2 PSI", "PT2"],
        "CHPV": ["CHPV"],
        "ECS PRI DUCT T (F)": ["ECS PRI DUCT T (F)", "ECS PRI DUCT T"],
        "ECS PRI DUCT T2 (F)": ["ECS PRI DUCT T2 (F)", "ECS PRI DUCT T2"],
        "ECS CKPT T (F)": ["ECS CKPT T (F)", "ECS CKPT T"],
        "O2 BTL Px PSI": ["O2 BTL Px PSI", "O2 BTL PRESS"],
        "O2 VLV Open": ["O2 VLV Open", "O2 VLV OPEN"],
        "EIPS TMP (F)": ["EIPS TMP (F)", "EIPS TMP"],
        "EIPS PRS PSI": ["EIPS PRS PSI", "EIPS PRS"]
    }

    for target_col, candidates in mappings.items():
        matched = next((c for c in candidates if c in df_raw.columns), None)
        if matched:
            s = pd.to_numeric(df_raw[matched], errors="coerce")
            if target_col in ["N1 %", "N2 %"] and s.dropna().max() <= 1.5:
                s = s * 100.0
            df_out[target_col] = s
        else:
            df_out[target_col] = np.nan

    return df_out
