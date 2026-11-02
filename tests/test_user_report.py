import sqlite3
from datetime import datetime, timedelta

import user_report


def _db(tmp_path, n_recent, n_old):
    p = str(tmp_path / 't.db')
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, created_at DATETIME)")
    now = datetime.utcnow()
    for _ in range(n_recent):
        c.execute("INSERT INTO user (created_at) VALUES (?)", (now.isoformat(sep=' '),))
    for _ in range(n_old):
        c.execute("INSERT INTO user (created_at) VALUES (?)", ((now - timedelta(days=30)).isoformat(sep=' '),))
    c.commit()
    c.close()
    return p


def test_gather_counts(tmp_path):
    assert user_report.gather(_db(tmp_path, 3, 2))[:3] == (5, 3, 3)


def test_alert_exit_status(tmp_path, monkeypatch):
    p = _db(tmp_path, 4, 0)
    monkeypatch.setattr('sys.argv', ['x', '--db', p, '--threshold-day', '3'])
    assert user_report.main() == 1
    monkeypatch.setattr('sys.argv', ['x', '--db', p])
    assert user_report.main() == 0


def test_register_rate_limit():
    import app
    app._register_attempts.clear()
    results = [app._register_rate_limited('1.2.3.4') for _ in range(app.REGISTER_LIMIT + 1)]
    assert results[-1] is True and not any(results[:-1])
