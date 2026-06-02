import csv
import random
from datetime import datetime, timedelta

random.seed(42)

ATTACK_TYPES = [
    ("Malware", 0.28),
    ("Phishing", 0.22),
    ("DDoS", 0.16),
    ("Ransomware", 0.14),
    ("SQL Injection", 0.09),
    ("Zero-Day Exploit", 0.06),
    ("Man-in-the-Middle", 0.05),
]

SOURCE_COUNTRIES = [
    ("Russia", 0.22), ("China", 0.20), ("North Korea", 0.10),
    ("Iran", 0.10), ("United States", 0.08), ("Ukraine", 0.07),
    ("Brazil", 0.05), ("India", 0.05), ("Germany", 0.04),
    ("Unknown", 0.09),
]

TARGET_COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France", "India",
    "Japan", "Australia", "Canada", "Brazil", "South Korea",
    "Italy", "Netherlands", "Spain", "Singapore", "UAE",
]

SECTORS = [
    ("Healthcare", 0.26), ("Finance", 0.22), ("Government", 0.18),
    ("Energy", 0.14), ("Education", 0.12), ("Retail", 0.08),
]

SEVERITIES = [
    ("Critical", 0.15), ("High", 0.30), ("Medium", 0.35), ("Low", 0.20),
]

STATUSES = [
    ("Blocked", 0.62), ("Mitigated", 0.21), ("Ongoing", 0.09), ("Resolved", 0.08),
]

def weighted_choice(choices):
    r = random.random()
    cumulative = 0
    for item, weight in choices:
        cumulative += weight
        if r <= cumulative:
            return item
    return choices[-1][0]

def generate_ip():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

rows = []
start_date = datetime(2024, 1, 1)

for i in range(1, 2001):
    date = start_date + timedelta(days=random.randint(0, 364), hours=random.randint(0,23), minutes=random.randint(0,59))
    attack = weighted_choice(ATTACK_TYPES)
    source = weighted_choice(SOURCE_COUNTRIES)
    target = random.choice(TARGET_COUNTRIES)
    sector = weighted_choice(SECTORS)
    severity = weighted_choice(SEVERITIES)
    status = weighted_choice(STATUSES)
    duration = random.randint(1, 720)  # minutes

    rows.append({
        "incident_id": f"INC-{i:05d}",
        "date": date.strftime("%Y-%m-%d"),
        "time": date.strftime("%H:%M:%S"),
        "attack_type": attack,
        "source_country": source,
        "target_country": target,
        "sector": sector,
        "severity": severity,
        "status": status,
        "source_ip": generate_ip(),
        "duration_minutes": duration,
        "data_breach": random.choice(["Yes", "Yes", "No", "No", "No"]),
    })

rows.sort(key=lambda x: x["date"])

with open("data/cyberattacks.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Generated {len(rows)} records → data/cyberattacks.csv")
