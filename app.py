from flask import (Flask, render_template, jsonify, request,
                   redirect, url_for, session, Response)
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, json, os, io, csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ctid-super-secret-2024-change-in-prod")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cyber.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_default_users():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            defaults = [
                ("admin",   generate_password_hash("admin123"),   "admin"),
                ("analyst", generate_password_hash("analyst123"), "analyst"),
                ("guest",   generate_password_hash("guest123"),   "guest"),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)",
                defaults
            )
            conn.commit()

init_default_users()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

def build_where(filters):
    conditions = ["source_country != 'Unknown'", "target_country != 'Unknown'"]
    params = []

    mappings = {
        "attack_type":    "attack_type = ?",
        "sector":         "sector = ?",
        "severity":       "severity = ?",
        "source_country": "source_country = ?",
    }
    for key, sql in mappings.items():
        val = filters.get(key)
        if val:
            conditions.append(sql)
            params.append(val)

    if filters.get("year"):
        conditions.append("strftime('%Y', date) = ?")
        params.append(filters["year"])

    if filters.get("month"):
        conditions.append("strftime('%Y-%m', date) = ?")
        params.append(filters["month"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return where, params


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("index"))
        error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html",
                           user=session.get("user"),
                           role=session.get("role"))

@app.route("/admin")
@login_required
def admin_panel():
    if session.get("role") != "admin":
        return redirect(url_for("index"))
    return render_template("admin.html",
                           user=session.get("user"),
                           role=session.get("role"))

@app.route("/about")
@login_required
def about():
    return render_template("about.html",
                           user=session.get("user"),
                           role=session.get("role"))


@app.route("/api/data")
@login_required
def api_data():
    filters = {
        "attack_type":    request.args.get("attack_type"),
        "sector":         request.args.get("sector"),
        "severity":       request.args.get("severity"),
        "source_country": request.args.get("source_country"),
        "year":           request.args.get("year"),
        "month":          request.args.get("month"),
    }

    where, params = build_where(filters)

    with get_db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM incidents {where}", params).fetchone()[0]
        if total == 0:
            return jsonify({"total_threats": 0})

        blocked = conn.execute(
            f"SELECT COUNT(*) FROM incidents {where} {'AND' if where else 'WHERE'} status='Blocked'",
            params
        ).fetchone()[0]

        breach = conn.execute(
            f"SELECT COUNT(*) FROM incidents {where} {'AND' if where else 'WHERE'} data_breach='Yes'",
            params
        ).fetchone()[0]

        avg_dur = conn.execute(
            f"SELECT ROUND(AVG(duration_minutes),1) FROM incidents {where}", params
        ).fetchone()[0] or 0

        rows = conn.execute(
            f"SELECT attack_type, COUNT(*) as cnt FROM incidents {where} GROUP BY attack_type ORDER BY cnt DESC LIMIT 10",
            params
        ).fetchall()
        attack_types = {r["attack_type"]: r["cnt"] for r in rows}

        rows = conn.execute(
            f"SELECT source_country, COUNT(*) as cnt FROM incidents {where} GROUP BY source_country ORDER BY cnt DESC LIMIT 10",
            params
        ).fetchall()
        source_countries = {r["source_country"]: r["cnt"] for r in rows}

        rows = conn.execute(
            f"SELECT target_country, COUNT(*) as cnt FROM incidents {where} GROUP BY target_country ORDER BY cnt DESC LIMIT 10",
            params
        ).fetchall()
        target_countries = {r["target_country"]: r["cnt"] for r in rows}

        rows = conn.execute(
            f"SELECT sector, COUNT(*) as cnt FROM incidents {where} GROUP BY sector ORDER BY cnt DESC LIMIT 10",
            params
        ).fetchall()
        sectors = {r["sector"]: r["cnt"] for r in rows}

        sev_order = ["Critical", "High", "Medium", "Low"]
        rows = conn.execute(
            f"SELECT severity, COUNT(*) as cnt FROM incidents {where} GROUP BY severity",
            params
        ).fetchall()
        sev_raw = {r["severity"]: r["cnt"] for r in rows}
        severity = {k: sev_raw[k] for k in sev_order if k in sev_raw}

        rows = conn.execute(
            f"SELECT status, COUNT(*) as cnt FROM incidents {where} GROUP BY status ORDER BY cnt DESC",
            params
        ).fetchall()
        statuses = {r["status"]: r["cnt"] for r in rows}

        rows = conn.execute(
            f"SELECT strftime('%Y-%m', date) as month, COUNT(*) as cnt FROM incidents {where} GROUP BY month ORDER BY month",
            params
        ).fetchall()
        monthly_trend = {r["month"]: r["cnt"] for r in rows}

        recent_rows = conn.execute(
            f"SELECT incident_id, date, attack_type, source_country, target_country, sector, severity, status FROM incidents {where} ORDER BY date DESC, time DESC LIMIT 10",
            params
        ).fetchall()
        recent = [dict(r) for r in recent_rows]

    return jsonify({
        "total_threats":    total,
        "blocked_attacks":  blocked,
        "block_rate":       round(blocked / total * 100, 1) if total else 0,
        "breach_count":     breach,
        "avg_duration_min": avg_dur,
        "attack_types":     attack_types,
        "source_countries": source_countries,
        "target_countries": target_countries,
        "sectors":          sectors,
        "severity":         severity,
        "statuses":         statuses,
        "monthly_trend":    monthly_trend,
        "recent_incidents": recent,
    })

@app.route("/api/filter-options")
@login_required
def filter_options():
    with get_db() as conn:
        attack_types = [r[0] for r in conn.execute(
            "SELECT DISTINCT attack_type FROM incidents WHERE attack_type IS NOT NULL ORDER BY attack_type"
        ).fetchall()]
        sectors = [r[0] for r in conn.execute(
            "SELECT DISTINCT sector FROM incidents WHERE sector IS NOT NULL ORDER BY sector"
        ).fetchall()]
        countries = [r[0] for r in conn.execute(
            "SELECT DISTINCT source_country FROM incidents WHERE source_country IS NOT NULL AND source_country != 'Unknown' ORDER BY source_country"
        ).fetchall()]
        years = [r[0] for r in conn.execute(
            "SELECT DISTINCT strftime('%Y', date) as y FROM incidents WHERE date IS NOT NULL ORDER BY y DESC"
        ).fetchall()]
        months_raw = [r[0] for r in conn.execute(
            "SELECT DISTINCT strftime('%Y-%m', date) as m FROM incidents WHERE date IS NOT NULL ORDER BY m DESC"
        ).fetchall()]

    month_options = []
    for m in months_raw:
        try:
            y, mo = m.split("-")
            label = datetime(int(y), int(mo), 1).strftime("%b %Y")
            month_options.append({"value": m, "label": label})
        except Exception:
            pass

    return jsonify({
        "attack_types":     attack_types,
        "sectors":          sectors,
        "severities":       ["Critical", "High", "Medium", "Low"],
        "source_countries": countries,
        "years":            years,
        "months":           month_options,
    })

@app.route("/api/incidents")
@login_required
def api_incidents():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    search   = request.args.get("search", "").strip()

    filters = {
        "attack_type":    request.args.get("attack_type"),
        "sector":         request.args.get("sector"),
        "severity":       request.args.get("severity"),
        "source_country": request.args.get("source_country"),
        "year":           request.args.get("year"),
        "month":          request.args.get("month"),
    }
    where, params = build_where(filters)

    if search:
        search_cond = """ AND (
            incident_id LIKE ? OR attack_type LIKE ? OR
            source_country LIKE ? OR target_country LIKE ? OR
            sector LIKE ? OR severity LIKE ? OR status LIKE ?
        )"""
        s = f"%{search}%"
        where = (where or "WHERE 1=1") + search_cond
        params += [s, s, s, s, s, s, s]

    with get_db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM incidents {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"""SELECT incident_id, date, time, attack_type, source_country,
                       target_country, sector, severity, status, duration_minutes, data_breach
                FROM incidents {where}
                ORDER BY date DESC, time DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()

    results = [dict(r) for r in rows]
    return jsonify({"total": total, "page": page, "per_page": per_page, "rows": results})

@app.route("/api/map-data")
@login_required
def api_map_data():
    with get_db() as conn:
        src_rows = conn.execute(
            "SELECT source_country, COUNT(*) as cnt FROM incidents WHERE source_country != 'Unknown' GROUP BY source_country ORDER BY cnt DESC LIMIT 20"
        ).fetchall()
        tgt_rows = conn.execute(
            "SELECT target_country, COUNT(*) as cnt FROM incidents WHERE target_country != 'Unknown' GROUP BY target_country ORDER BY cnt DESC LIMIT 20"
        ).fetchall()

    src = {r["source_country"]: r["cnt"] for r in src_rows}
    tgt = {r["target_country"]: r["cnt"] for r in tgt_rows}
    combined = {}
    for c, n in src.items(): combined[c] = combined.get(c, 0) + n
    for c, n in tgt.items(): combined[c] = combined.get(c, 0) + n

    return jsonify({"source_countries": src, "target_countries": tgt, "combined": combined})

@app.route("/api/alerts")
@login_required
def api_alerts():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT incident_id, date, attack_type, source_country, target_country, sector, severity, status
               FROM incidents
               WHERE severity IN ('Critical','High') AND status = 'Ongoing'
               ORDER BY date DESC LIMIT 5"""
        ).fetchall()
    alerts = [dict(r) for r in rows]
    return jsonify({"alerts": alerts, "count": len(alerts)})

@app.route("/api/export/csv")
@login_required
def export_csv():
    filters = {
        "attack_type":    request.args.get("attack_type"),
        "sector":         request.args.get("sector"),
        "severity":       request.args.get("severity"),
        "source_country": request.args.get("source_country"),
        "year":           request.args.get("year"),
        "month":          request.args.get("month"),
    }
    where, params = build_where(filters)

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT incident_id, date, attack_type, source_country, target_country,
                       sector, severity, status, duration_minutes, data_breach
                FROM incidents {where} ORDER BY date DESC""",
            params
        ).fetchall()

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for r in rows:
            writer.writerow(dict(r))

    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=cyber_incidents_export.csv"})



@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY id"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role     = data.get("role", "guest")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if role not in ("admin", "analyst", "guest"):
        return jsonify({"error": "Invalid role"}), 400

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (username, generate_password_hash(password), role)
            )
            conn.commit()
        return jsonify({"success": True, "message": f"User '{username}' created"})
    except Exception:
        return jsonify({"error": "Username already exists"}), 409

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    with get_db() as conn:
        user = conn.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user["username"] == session.get("user"):
            return jsonify({"error": "Cannot delete your own account"}), 400
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    return jsonify({"success": True})

@app.route("/api/users/<int:user_id>/password", methods=["PUT"])
@admin_required
def change_password(user_id):
    data         = request.get_json()
    new_password = data.get("password", "").strip()
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (generate_password_hash(new_password), user_id)
        )
        conn.commit()
    return jsonify({"success": True})

@app.route("/api/db-stats")
@admin_required
def db_stats():
    with get_db() as conn:
        total      = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        users      = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        date_range = conn.execute("SELECT MIN(date), MAX(date) FROM incidents").fetchone()
        attack_types = conn.execute("SELECT COUNT(DISTINCT attack_type) FROM incidents").fetchone()[0]
        countries    = conn.execute("SELECT COUNT(DISTINCT source_country) FROM incidents").fetchone()[0]

    return jsonify({
        "total_incidents": total,
        "total_users":     users,
        "date_from":       date_range[0],
        "date_to":         date_range[1],
        "attack_types":    attack_types,
        "countries":       countries,
        "db_path":         DB_PATH,
    })

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)