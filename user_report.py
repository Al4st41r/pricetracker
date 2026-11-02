"""Report on pricetracker user numbers and flag unusual growth.

Usage: uv run user_report.py [--threshold-total N] [--threshold-day N] [--log FILE]

Exit status is 1 when a threshold is exceeded, so it can be run from cron
(output is only needed when the status is non-zero, e.g. via MAILTO).
Defaults can be set with USER_ALERT_TOTAL and USER_ALERT_DAY.
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'pricetracker.db')


def gather(db_path):
    conn = sqlite3.connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        cols = [r[1] for r in conn.execute("PRAGMA table_info(user)")]
        day = week = unknown = None
        if 'created_at' in cols:
            now = datetime.utcnow()
            q = "SELECT COUNT(*) FROM user WHERE created_at >= ?"
            day = conn.execute(q, ((now - timedelta(days=1)).isoformat(sep=' '),)).fetchone()[0]
            week = conn.execute(q, ((now - timedelta(days=7)).isoformat(sep=' '),)).fetchone()[0]
            unknown = conn.execute("SELECT COUNT(*) FROM user WHERE created_at IS NULL").fetchone()[0]
        return total, day, week, unknown
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--threshold-total', type=int, default=int(os.environ.get('USER_ALERT_TOTAL', 100)))
    ap.add_argument('--threshold-day', type=int, default=int(os.environ.get('USER_ALERT_DAY', 10)))
    ap.add_argument('--log', help='append the summary line to this file')
    ap.add_argument('--db', default=DB)
    a = ap.parse_args()

    total, day, week, unknown = gather(a.db)
    line = (f"{datetime.utcnow():%Y-%m-%d %H:%M} users total={total} last24h={day} "
            f"last7d={week} undated={unknown}")
    alerts = []
    if total >= a.threshold_total:
        alerts.append(f"total users {total} >= {a.threshold_total}")
    if day is not None and day >= a.threshold_day:
        alerts.append(f"{day} sign-ups in 24h >= {a.threshold_day}")
    if alerts:
        line += " ALERT: " + "; ".join(alerts)
    print(line)
    if a.log:
        with open(a.log, 'a') as f:
            f.write(line + "\n")
    return 1 if alerts else 0


if __name__ == '__main__':
    sys.exit(main())
