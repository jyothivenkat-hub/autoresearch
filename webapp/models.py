"""SQLite database layer for Twitter optimizer."""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "twitter_optimizer.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            post_id TEXT,
            date TEXT,
            post_text TEXT,
            post_link TEXT,
            impressions INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            engagements INTEGER DEFAULT 0,
            bookmarks INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            new_follows INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0,
            profile_visits INTEGER DEFAULT 0,
            detail_expands INTEGER DEFAULT 0,
            url_clicks INTEGER DEFAULT 0,
            hashtag_clicks INTEGER DEFAULT 0,
            permalink_clicks INTEGER DEFAULT 0,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            experiment_name TEXT,
            description TEXT,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_seconds REAL,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        );

        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            tweet_text TEXT,
            strategy TEXT,
            reasoning TEXT,
            target_metric TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        );
    """)
    conn.commit()
    conn.close()


def save_upload(filename, row_count):
    conn = get_db()
    cur = conn.execute("INSERT INTO uploads (filename, row_count) VALUES (?, ?)",
                       (filename, row_count))
    upload_id = cur.lastrowid
    conn.commit()
    conn.close()
    return upload_id


def save_posts(upload_id, posts_df):
    conn = get_db()
    for _, row in posts_df.iterrows():
        conn.execute("""
            INSERT INTO posts (upload_id, post_id, date, post_text, post_link,
                impressions, likes, engagements, bookmarks, shares, new_follows,
                replies, reposts, profile_visits, detail_expands, url_clicks,
                hashtag_clicks, permalink_clicks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            upload_id,
            str(row.get('Post id', '')),
            str(row.get('Date', '')),
            str(row.get('Post text', '')),
            str(row.get('Post Link', '')),
            int(row.get('Impressions', 0)),
            int(row.get('Likes', 0)),
            int(row.get('Engagements', 0)),
            int(row.get('Bookmarks', 0)),
            int(row.get('Shares', 0)),
            int(row.get('New follows', 0)),
            int(row.get('Replies', 0)),
            int(row.get('Reposts', 0)),
            int(row.get('Profile visits', 0)),
            int(row.get('Detail Expands', 0)),
            int(row.get('URL Clicks', 0)),
            int(row.get('Hashtag Clicks', 0)),
            int(row.get('Permalink Clicks', 0)),
        ))
    conn.commit()
    conn.close()


def get_latest_upload():
    conn = get_db()
    row = conn.execute("SELECT * FROM uploads ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def get_posts(upload_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM posts WHERE upload_id = ? ORDER BY impressions DESC",
                        (upload_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_experiment(upload_id, name, description, result, time_seconds):
    conn = get_db()
    conn.execute("""
        INSERT INTO experiments (upload_id, experiment_name, description, result_json, time_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (upload_id, name, description, json.dumps(result), time_seconds))
    conn.commit()
    conn.close()


def get_experiments(upload_id=None):
    conn = get_db()
    if upload_id:
        rows = conn.execute("SELECT * FROM experiments WHERE upload_id = ? ORDER BY id DESC",
                            (upload_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM experiments ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_suggestions(upload_id, suggestions):
    conn = get_db()
    for s in suggestions:
        conn.execute("""
            INSERT INTO suggestions (upload_id, tweet_text, strategy, reasoning, target_metric)
            VALUES (?, ?, ?, ?, ?)
        """, (upload_id, s.get('tweet', ''), s.get('strategy', ''),
              s.get('reasoning', ''), s.get('target_metric', '')))
    conn.commit()
    conn.close()


def get_suggestions(upload_id=None, unused_only=False):
    conn = get_db()
    query = "SELECT * FROM suggestions"
    params = []
    conditions = []
    if upload_id:
        conditions.append("upload_id = ?")
        params.append(upload_id)
    if unused_only:
        conditions.append("used = 0")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_suggestion_used(suggestion_id):
    conn = get_db()
    conn.execute("UPDATE suggestions SET used = 1 WHERE id = ?", (suggestion_id,))
    conn.commit()
    conn.close()
