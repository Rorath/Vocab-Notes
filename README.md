# Vocab-Notes
A small Flask site for collecting words by group and practising them with flashcards.
Words and review progress are saved in `vocab.db` beside the application.

## Running it

Double-click `launch.command` (or the "Launch Vocab-Notes" shortcut on your
Desktop). It sets up the environment on first run, starts the app, and opens
http://127.0.0.1:5001 in your browser. Press Ctrl+C in the Terminal window to stop.

To run it manually:

```bash
python3 -m venv venv        # first time only
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5001 after starting it manually. To run the local
development server on another interface, set `VOCAB_HOST` explicitly.

## Checks

```bash
venv/bin/python -m unittest discover -s tests -v
node --check static/main.js
```
