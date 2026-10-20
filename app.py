import json
import os
from urllib.parse import urlsplit
from flask import Flask, abort, render_template, request, redirect, url_for, jsonify
from database import (
    init_db, add_word, get_all_words, get_word, delete_word, update_word,
    get_categories, get_ungrouped_words, get_group_summary, set_words_category,
    find_word_by_name, get_unfamiliar_words, record_result,
    get_today_count, get_daily_goal, set_daily_goal,
)

app = Flask(__name__)
init_db()

def load_list(raw):
    """Parse a stored JSON array into a list of strings (robust to legacy/plain values)."""
    if not raw:
        return []
    try:
        val = json.loads(raw)
    except (ValueError, TypeError):
        return [str(raw)]
    if isinstance(val, list):
        return [str(v) for v in val if str(v).strip()]
    return [str(val)]

app.jinja_env.filters["as_list"] = load_list

@app.route("/")
def index():
    return render_template("groups.html", summary=get_group_summary())

@app.route("/words")
def words():
    category = request.args.get("category") or None
    ungrouped = bool(request.args.get("ungrouped"))
    review = bool(request.args.get("review"))
    sort = request.args.get("sort", "priority" if review else "recent")
    if not review and sort == "priority":
        sort = "recent"
    search = request.args.get("q", "").strip()
    if review:
        word_list = get_unfamiliar_words(sort, search)
        title = "Needs review"
    elif ungrouped:
        word_list = get_ungrouped_words(sort, search)
        title = "Ungrouped"
    else:
        word_list = get_all_words(sort, category, search)
        title = category or "All Words"
    return render_template(
        "index.html",
        words=word_list,
        current_sort=sort,
        current_category=category,
        ungrouped=ungrouped,
        review=review,
        search=search,
        title=title,
        categories=get_categories(),
    )

@app.route("/bulk-group", methods=["POST"])
def bulk_group():
    ids = request.form.getlist("ids", type=int)
    category = request.form.get("category", "").strip()
    set_words_category(ids, category)
    return _redirect_after_save(category)

@app.route("/list")
def collection():
    sort = request.args.get("sort", "recent")
    search = request.args.get("q", "").strip()
    words = get_all_words(sort, search=search)
    return render_template("list.html", words=words, current_sort=sort, search=search)

def _redirect_after_save(category):
    """Send the user back into the group they were working in."""
    if category:
        return redirect(url_for("words", category=category))
    return redirect(url_for("words"))

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        word = request.form.get("word", "").strip()
        english_defs = [d.strip() for d in request.form.getlist("english_def") if d.strip()]
        chinese_def = request.form.get("chinese_def", "").strip()
        examples = [e.strip() for e in request.form.getlist("examples") if e.strip()]
        category = request.form.get("category", "").strip()
        if not word:
            return render_template(
                "add.html", categories=get_categories(),
                error="Enter a word before saving.", form_word=word,
                english_defs=english_defs, chinese_def=chinese_def,
                examples=examples, category=category,
            ), 400
        existing = find_word_by_name(word)
        if existing:
            return render_template(
                "add.html",
                categories=get_categories(),
                error='“%s” is already in your vocabulary. '
                      'Edit the existing entry instead of adding a duplicate.' % existing["word"],
                existing_id=existing["id"],
                form_word=word,
                english_defs=english_defs,
                chinese_def=chinese_def,
                examples=examples,
                category=category,
            )
        add_word(word, english_defs, chinese_def, examples, category)
        return _redirect_after_save(category)
    return render_template("add.html", categories=get_categories())

@app.route("/edit/<int:word_id>", methods=["GET", "POST"])
def edit(word_id):
    word = get_word(word_id)
    if word is None:
        abort(404)
    if request.method == "POST":
        new_word = request.form.get("word", "").strip()
        category = request.form.get("category", "").strip()
        english_defs = [d.strip() for d in request.form.getlist("english_def") if d.strip()]
        examples = [e.strip() for e in request.form.getlist("examples") if e.strip()]
        if not new_word:
            return render_template(
                "add.html", word=word, categories=get_categories(),
                error="Enter a word before saving.", form_word=new_word,
                english_defs=english_defs, examples=examples,
                chinese_def=request.form.get("chinese_def", "").strip(),
                category=category,
            ), 400
        clash = find_word_by_name(new_word, exclude_id=word_id)
        if clash:
            return render_template(
                "add.html",
                word=word,
                english_defs=english_defs,
                examples=examples,
                categories=get_categories(),
                error='“%s” already exists as another entry, so this rename '
                      'would create a duplicate.' % clash["word"],
                form_word=new_word,
                chinese_def=request.form.get("chinese_def", "").strip(),
                category=category,
            )
        update_word(
            word_id,
            new_word,
            english_defs,
            request.form.get("chinese_def", "").strip(),
            examples,
            category,
        )
        return _redirect_after_save(category)
    return render_template(
        "add.html",
        word=word,
        english_defs=load_list(word["english_defs"]) if word else [],
        examples=load_list(word["examples"]) if word else [],
        categories=get_categories(),
    )

@app.route("/delete/<int:word_id>", methods=["POST"])
def delete(word_id):
    delete_word(word_id)
    referrer = request.referrer
    if referrer and urlsplit(referrer).netloc == request.host:
        return redirect(referrer)
    return redirect(url_for("index"))

@app.route("/learn")
def learn():
    category = request.args.get("category") or None
    words = get_all_words("recent", category)
    word_payload = [
        {"id": w["id"], "word": w["word"],
         "english_defs": load_list(w["english_defs"]),
         "chinese_def": w["chinese_def"],
         "examples": load_list(w["examples"]),
         "familiarity": w["familiarity"]}
        for w in words
    ]
    return render_template(
        "learn.html",
        words=words,
        word_payload=word_payload,
        categories=get_categories(),
        current_category=category,
        today_count=get_today_count(),
        daily_goal=get_daily_goal(),
    )

@app.route("/api/result", methods=["POST"])
def api_result():
    """Record a flashcard answer: {id, known: bool}. Updates familiarity + today's tally."""
    data = request.get_json(silent=True) or {}
    try:
        word_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"error": "bad id"}), 400
    known = data.get("known")
    if not isinstance(known, bool):
        return jsonify({"error": "known must be a boolean"}), 400
    fam = record_result(word_id, known)
    if fam is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "familiarity": fam,
        "today": get_today_count(),
        "goal": get_daily_goal(),
    })

@app.route("/api/goal", methods=["POST"])
def api_goal():
    """Set (or clear, with 0) the optional reviews-per-day goal."""
    data = request.get_json(silent=True) or {}
    goal = set_daily_goal(data.get("goal", 0))
    return jsonify({"goal": goal, "today": get_today_count()})

@app.route("/api/words")
def api_words():
    words = get_all_words()
    return jsonify([
        {**dict(w),
         "english_defs": load_list(w["english_defs"]),
         "examples": load_list(w["examples"])}
        for w in words
    ])

if __name__ == "__main__":
    # Local dev defaults to 5001; hosts that inject a PORT env var override it.
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1",
            host=os.environ.get("VOCAB_HOST", "127.0.0.1"), port=port)
