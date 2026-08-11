import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import (
    init_db, add_word, get_all_words, get_word, delete_word, update_word,
    get_categories, get_ungrouped_words, get_group_summary,
)

app = Flask(__name__)

@app.before_request
def setup():
    init_db()

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
    )

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
        english_def = request.form["english_def"].strip()
        chinese_def = request.form.get("chinese_def", "").strip()
        sentence = request.form.get("sentence", "").strip()
        category = request.form.get("category", "").strip()
        add_word(word, english_def, chinese_def, sentence, category)
        return _redirect_after_save(category)
    return render_template("add.html", categories=get_categories())

@app.route("/edit/<int:word_id>", methods=["GET", "POST"])
def edit(word_id):
    word = get_word(word_id)
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        update_word(
            word_id,
            request.form["word"].strip(),
            request.form["english_def"].strip(),
            request.form.get("chinese_def", "").strip(),
            request.form.get("sentence", "").strip(),
            category,
        )
        return _redirect_after_save(category)
    return render_template("add.html", word=word, categories=get_categories())

@app.route("/delete/<int:word_id>", methods=["POST"])
def delete(word_id):
    delete_word(word_id)
    return redirect(request.referrer or url_for("index"))

@app.route("/learn")
def learn():
    category = request.args.get("category") or None
    words = get_all_words("recent", category)
    words_json = json.dumps([dict(w) for w in words])
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
    return jsonify([dict(w) for w in words])

if __name__ == "__main__":
    app.run(debug=True)
