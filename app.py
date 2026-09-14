import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import (
    init_db, add_word, get_all_words, get_word, delete_word, update_word,
    get_categories, get_ungrouped_words, get_group_summary, set_words_category,
    find_word_by_name,
)

app = Flask(__name__)

@app.before_request
def setup():
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
    sort = request.args.get("sort", "recent")
    category = request.args.get("category") or None
    ungrouped = bool(request.args.get("ungrouped"))
    if ungrouped:
        word_list = get_ungrouped_words(sort)
        title = "Ungrouped"
    else:
        word_list = get_all_words(sort, category)
        title = category or "All Words"
    return render_template(
        "index.html",
        words=word_list,
        current_sort=sort,
        current_category=category,
        ungrouped=ungrouped,
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
    words = get_all_words(sort)
    return render_template("list.html", words=words, current_sort=sort)

def _redirect_after_save(category):
    """Send the user back into the group they were working in."""
    if category:
        return redirect(url_for("words", category=category))
    return redirect(url_for("words"))

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        word = request.form["word"].strip()
        english_defs = [d.strip() for d in request.form.getlist("english_def") if d.strip()]
        chinese_def = request.form.get("chinese_def", "").strip()
        examples = [e.strip() for e in request.form.getlist("examples") if e.strip()]
        category = request.form.get("category", "").strip()
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
    if request.method == "POST":
        new_word = request.form["word"].strip()
        category = request.form.get("category", "").strip()
        english_defs = [d.strip() for d in request.form.getlist("english_def") if d.strip()]
        examples = [e.strip() for e in request.form.getlist("examples") if e.strip()]
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
    return redirect(request.referrer or url_for("index"))

@app.route("/learn")
def learn():
    category = request.args.get("category") or None
    words = get_all_words("recent", category)
    words_json = json.dumps([
        {**dict(w),
         "english_defs": load_list(w["english_defs"]),
         "examples": load_list(w["examples"])}
        for w in words
    ])
    return render_template(
        "learn.html",
        words=words,
        words_json=words_json,
        categories=get_categories(),
        current_category=category,
    )

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
    app.run(debug=True, port=5001)
