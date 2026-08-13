import json
import os
import random
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)

# set SECRET_KEY as environment variable
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-fallback-change-in-production")

# ── Data Loading ──────────────────────────────────────────────────────────────

def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

TOPICS    = load_json("topics.json")["topics"]
QUESTIONS = load_json("questions.json")["questions"]

# ── Session Helpers ───────────────────────────────────────────────────────────

def init_session():
    """Ensure all session keys exist."""
    if "streak" not in session:
        session["streak"] = 0
    if "last_activity" not in session:
        session["last_activity"] = None
    if "completed_topics" not in session:
        session["completed_topics"] = []
    if "total_stars" not in session:
        session["total_stars"] = 0
    if "lessons_today" not in session:
        session["lessons_today"] = 0
    if "lessons_today_date" not in session:
        session["lessons_today_date"] = str(date.today())


def update_streak():
    """Update the streak counter based on today's activity."""
    today = str(date.today())
    last  = session.get("last_activity")

    # Reset daily lesson counter if it's a new day
    if session.get("lessons_today_date") != today:
        session["lessons_today"]      = 0
        session["lessons_today_date"] = today

    if last is None:
        session["streak"]        = 1
        session["last_activity"] = today
    elif last == today:
        pass  # already counted today
    else:
        last_date  = datetime.strptime(last, "%Y-%m-%d").date()
        today_date = date.today()
        if (today_date - last_date).days == 1:
            session["streak"]       += 1
        else:
            session["streak"]        = 1
        session["last_activity"] = today

    session["lessons_today"] = session.get("lessons_today", 0) + 1
    session.modified = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    init_session()
    completed = session.get("completed_topics", [])

    # Build enriched topic list
    topics_with_status = [
        {
            **t,
            "completed": t["id"] in completed,
            "question_count": len(QUESTIONS.get(str(t["id"]), [])),
        }
        for t in TOPICS
    ]

    # Group topics by grade (1–6), deriving grade solely from topics.json
    grades = []
    for grade_num in range(1, 7):
        grade_topics = [t for t in topics_with_status if t["grade"] == grade_num]
        grades.append({"num": grade_num, "topics": grade_topics})

    # Append the mixed grade group (grade 99) after the numbered grades
    mixed_topics = [t for t in topics_with_status if t["grade"] == 99]
    if mixed_topics:
        grades.append({"num": 99, "topics": mixed_topics})

    return render_template(
        "home.html",
        grades=grades,
        streak=session["streak"],
        total_stars=session["total_stars"],
        lessons_today=session.get("lessons_today", 0),
    )


@app.route("/lesson/<topic_id>")
def lesson(topic_id):
    init_session()
    topic = next((t for t in TOPICS if t["id"] == topic_id), None)
    if not topic:
        return render_template("404.html"), 404
    questions = random.sample(QUESTIONS.get(topic_id, []), k=len(QUESTIONS.get(topic_id, [])))
    return render_template(
        "lesson.html",
        topic=topic,
        questions=questions,
        streak=session["streak"],
        total_stars=session["total_stars"],
    )


@app.route("/api/complete_lesson", methods=["POST"])
def complete_lesson():
    """Called by JS when a lesson quiz is finished."""
    init_session()
    data        = request.get_json()
    topic_id    = data.get("topic_id")
    correct     = data.get("correct", 0)
    total       = data.get("total", 0)
    stars_earned = _calc_stars(correct, total)

    # Update streak
    update_streak()

    # Track completed topics (can repeat; just keep unique set)
    completed = session.get("completed_topics", [])
    if topic_id not in completed:
        completed.append(topic_id)
        session["completed_topics"] = completed

    session["total_stars"] = session.get("total_stars", 0) + stars_earned
    session.modified = True

    return jsonify({
        "streak":      session["streak"],
        "total_stars": session["total_stars"],
        "stars_earned": stars_earned,
        "correct":     correct,
        "total":       total,
    })


@app.route("/api/session_data")
def session_data():
    init_session()
    return jsonify({
        "streak":           session["streak"],
        "total_stars":      session["total_stars"],
        "completed_topics": session["completed_topics"],
        "lessons_today":    session.get("lessons_today", 0),
    })


@app.route("/api/reset")
def reset_session():
    session.clear()
    return jsonify({"status": "ok"})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _calc_stars(correct, total):
    if total == 0:
        return 0
    pct = correct / total
    if pct >= 0.9:
        return 3
    elif pct >= 0.6:
        return 2
    else:
        return 1


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
