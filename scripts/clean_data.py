import pandas as pd
import json
import os

CSV_PATH = "data/cyberattacks.csv"
OUT_PATH  = "data/summary.json"

print(f"Loading {CSV_PATH} ...")
df = pd.read_csv(CSV_PATH)
print(f"  Rows loaded : {len(df)}")
print(f"  Columns     : {df.columns.tolist()}\n")

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

REQUIRED = ["attack_type", "source_country", "sector", "severity", "status"]
for col in REQUIRED:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found. Edit the COLUMN MAP above.")


before = len(df)
df.dropna(subset=REQUIRED, inplace=True)
df[REQUIRED] = df[REQUIRED].apply(lambda c: c.str.strip())
print(f"Rows after cleaning: {len(df)}  (dropped {before - len(df)} blank rows)")


if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year"]  = df["date"].dt.year.astype(str)
else:
    df["month"] = "2024-01"
    df["year"]  = "2024"


def top(series, n=10):
    return series.value_counts().head(n).to_dict()

monthly_raw = df.groupby("month").size()
monthly_trend = {k: int(v) for k, v in monthly_raw.items()}

severity_order = ["Critical", "High", "Medium", "Low"]
severity_counts = {
    s: int(df[df["severity"] == s].shape[0])
    for s in severity_order if s in df["severity"].values
}

blocked     = int(df[df["status"] == "Blocked"].shape[0])
block_rate  = round(blocked / len(df) * 100, 1) if len(df) else 0

breach_count = int(df[df["data_breach"] == "Yes"].shape[0]) if "data_breach" in df.columns else 0

avg_duration = round(df["duration_minutes"].mean(), 1) if "duration_minutes" in df.columns else 0

summary = {
    "total_threats"    : int(len(df)),
    "blocked_attacks"  : blocked,
    "block_rate"       : block_rate,
    "breach_count"     : breach_count,
    "avg_duration_min" : avg_duration,
    "attack_types"     : {k: int(v) for k, v in top(df["attack_type"]).items()},
    "source_countries" : {k: int(v) for k, v in top(df["source_country"]).items()},
    "target_countries" : {k: int(v) for k, v in top(df["target_country"]).items()},
    "sectors"          : {k: int(v) for k, v in top(df["sector"]).items()},
    "severity"         : severity_counts,
    "statuses"         : {k: int(v) for k, v in top(df["status"]).items()},
    "monthly_trend"    : monthly_trend,
    "recent_incidents" : df.sort_values("date", ascending=False).head(20)[
        ["incident_id", "date", "attack_type", "source_country",
         "target_country", "sector", "severity", "status"]
    ].assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d")).to_dict(orient="records"),
}

os.makedirs("data", exist_ok=True)
with open(OUT_PATH, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n✅  summary.json saved → {OUT_PATH}")
print(f"   Total threats  : {summary['total_threats']:,}")
print(f"   Block rate     : {summary['block_rate']}%")
print(f"   Data breaches  : {summary['breach_count']}")
