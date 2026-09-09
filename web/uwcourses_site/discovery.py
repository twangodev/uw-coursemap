"""Disposable website indexes for course discovery and original student reviews."""

import json

GRADE_KEYS = ["a", "ab", "b", "bc", "c", "d", "f"]


def build_discovery(db, reviews):
    db.executescript("""
    CREATE TABLE course_numbers(uid TEXT PRIMARY KEY,number INTEGER);
    CREATE TABLE offerings(uid TEXT,term TEXT,PRIMARY KEY(uid,term));
    CREATE TABLE grade_summaries(uid TEXT,term TEXT,a INTEGER,ab INTEGER,b INTEGER,bc INTEGER,c INTEGER,d INTEGER,f INTEGER,PRIMARY KEY(uid,term));
    CREATE TABLE reviews(profile_id TEXT,review_id TEXT,course_uid TEXT,review_date TEXT,payload TEXT,PRIMARY KEY(profile_id,review_id));
    CREATE INDEX reviews_profile_date ON reviews(profile_id,review_date DESC,review_id);
    CREATE INDEX offerings_term ON offerings(term,uid);
    """)
    for uid, payload in db.execute("SELECT uid,payload FROM courses"):
        course = json.loads(payload)
        db.execute(
            "INSERT INTO course_numbers VALUES(?,?)", (uid, course.get("course_number"))
        )
        db.executemany(
            "INSERT OR IGNORE INTO offerings VALUES(?,?)",
            [(uid, row["term_id"]) for row in course["offerings"]],
        )
    columns = ",".join(
        f"COALESCE(json_extract(payload,'$.{key}'),0)" for key in GRADE_KEYS
    )
    db.execute(
        f"INSERT INTO grade_summaries SELECT uid,term,{columns} FROM grades WHERE section='' "
    )
    latest = {}
    for row in reviews:
        key = (row["source_instructor_id"], row["source_review_id"])
        if key not in latest or str(row["observed_at"]) > str(
            latest[key]["observed_at"]
        ):
            latest[key] = row
    db.executemany(
        "INSERT INTO reviews VALUES(?,?,?,?,?)",
        [
            (
                profile,
                review,
                row.get("course_uid"),
                str(row.get("review_date") or ""),
                json.dumps(row, default=str, ensure_ascii=False),
            )
            for (profile, review), row in latest.items()
        ],
    )
