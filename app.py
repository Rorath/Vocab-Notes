import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, add_word, get_all_words, get_word, delete_word, update_word, get_categories

app = Flask(__name__)

@app.before_request
def setup():
    init_db()

@app.route("/")
def index():
    sort = request.args.get("sort", "recent")
    category = request.args.get("category") or None
    words = get_all_words(sort, category)
    return render_template(
        "index.html",
        words=words,
        categories=get_categories(),
        current_sort=sort,
        current_category=category,
    )

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        word = request.form["word"].strip()
        english_def = request.form["english_def"].strip()
        chinese_def = request.form.get("chinese_def", "").strip()
        sentence = request.form.get("sentence", "").strip()
        category = request.form.get("category", "").strip()
        add_word(word, english_def, chinese_def, sentence, category)
        return redirect(url_for("index"))
    return render_template("add.html", categories=get_categories())

@app.route("/edit/<int:word_id>", methods=["GET", "POST"])
def edit(word_id):
    word = get_word(word_id)
    if request.method == "POST":
        update_word(
            word_id,
            request.form["word"].strip(),
            request.form["english_def"].strip(),
            request.form.get("chinese_def", "").strip(),
            request.form.get("sentence", "").strip(),
            request.form.get("category", "").strip(),
        )
        return redirect(url_for("index"))
    return render_template("add.html", word=word, categories=get_categories())

@app.route("/delete/<int:word_id>", methods=["POST"])
def delete(word_id):
    delete_word(word_id)
    return redirect(url_for("index"))

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
