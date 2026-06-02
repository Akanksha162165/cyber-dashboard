# 🛡️ Cyber Threat Intelligence Dashboard

A full-stack web application that visualises real-world cybersecurity attack data using interactive charts, a searchable incident table, and role-based user authentication.

---

## 📌 Project Overview

| Field        | Details |
|-------------|---------|
| **Title**   | Cyber Threat Intelligence Dashboard |
| **Domain**  | Data Analytics + Cybersecurity |
| **Stack**   | Python, Flask, Pandas, HTML, CSS, JavaScript, Chart.js |
| **Deployment** | Render.com (free) |

---

## 🎯 Features

- 🔐 **Login system** with 3 user roles (Admin, Analyst, Guest)
- 📊 **6 interactive charts** — Doughnut, Line, Bar charts
- 🔍 **Real-time filters** — by attack type, sector, severity, country
- 📋 **Paginated incident table** with live search
- 🌐 **REST API** (`/api/data`, `/api/incidents`, `/api/filter-options`)
- 📱 **Responsive design** — works on mobile and desktop
- 🎨 **Dark cybersecurity theme**

---

## 🗂️ Project Structure

```
cyber-threat-dashboard/
├── data/
│   ├── cyberattacks.csv       ← Raw dataset (2000 records)
│   └── summary.json           ← Pre-processed summary (auto-generated)
├── scripts/
│   ├── generate_sample_data.py  ← Generates the CSV dataset
│   └── clean_data.py            ← Cleans CSV → produces summary.json
├── static/
│   ├── css/style.css            ← Dark theme stylesheet
│   └── js/charts.js             ← Chart.js logic + API calls
├── templates/
│   ├── login.html               ← Login page
│   └── index.html               ← Main dashboard
├── app.py                       ← Flask backend + API routes
├── requirements.txt
├── Procfile                     ← For Render/Heroku deployment
└── README.md
```

---

## 🚀 Setup & Run (Local)

### Step 1 — Clone / download the project
```bash
git clone https://github.com/YOUR_USERNAME/cyber-dashboard.git
cd cyber-dashboard
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Generate the dataset
```bash
python scripts/generate_sample_data.py
```
> This creates `data/cyberattacks.csv` with 2000 realistic incidents.
> **Optional:** Replace with your own Kaggle dataset (see "Using Your Own Dataset" below).

### Step 4 — Clean the data
```bash
python scripts/clean_data.py
```
> This produces `data/summary.json` which the Flask API serves.

### Step 5 — Run the app
```bash
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000**

---

## 🔑 Login Credentials (Demo)

| Username | Password   | Role     |
|----------|------------|----------|
| admin    | admin123   | Admin    |
| analyst  | analyst123 | Analyst  |
| guest    | guest123   | Guest    |

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data` | GET | Main chart data. Supports filters: `attack_type`, `sector`, `severity`, `source_country` |
| `/api/incidents` | GET | Paginated incident rows. Supports `page`, `per_page`, `search` |
| `/api/filter-options` | GET | Returns unique values for each filter dropdown |
| `/api/stats/summary` | GET | Quick stat card numbers |

**Filter example:**
```
GET /api/data?attack_type=Ransomware&sector=Healthcare
```

---

## 🗃️ Using Your Own Kaggle Dataset

1. Download a cybersecurity dataset from [kaggle.com](https://kaggle.com) (search: "cybersecurity attacks")
2. Save the CSV as `data/cyberattacks.csv`
3. Open `scripts/clean_data.py` and update the **COLUMN MAP** section to match your column names
4. Re-run `python scripts/clean_data.py`

---

## ☁️ Deployment on Render.com (Free)

1. Push project to GitHub:
   ```bash
   git init && git add . && git commit -m "first commit"
   git remote add origin https://github.com/YOUR_USERNAME/cyber-dashboard.git
   git push -u origin main
   ```

2. Go to [render.com](https://render.com) → Sign in with GitHub

3. Click **New → Web Service** → Select your repo

4. Settings:
   - **Build Command:** `pip install -r requirements.txt && python scripts/generate_sample_data.py && python scripts/clean_data.py`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3

5. Click **Deploy** — you'll get a free public URL in ~2 minutes!

---

## 🔧 Technologies Used

| Technology | Purpose |
|-----------|---------|
| Python 3  | Backend logic, data processing |
| Flask     | Web framework, REST API |
| Pandas    | CSV loading, data cleaning, aggregation |
| Chart.js  | Interactive charts in browser |
| HTML/CSS  | Frontend UI + dark theme |
| JavaScript (Vanilla) | API calls, filter logic, DOM updates |
| Gunicorn  | Production web server |
| Render.com | Free cloud hosting |

---

## 📈 Charts Included

1. **Attack Types Distribution** — Doughnut chart
2. **Monthly Threat Trend** — Line chart
3. **Top Source Countries** — Horizontal bar chart
4. **Most Targeted Sectors** — Vertical bar chart
5. **Severity Breakdown** — Doughnut chart
6. **Attack Status** — Doughnut chart

---

## 👤 Author

**[Your Name]**
Final Year Project — [Your College Name]
[Year]
