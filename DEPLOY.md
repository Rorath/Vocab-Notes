# Deploying Vocab-Notes (so your phone can reach it 24/7)

The goal: run the app on a machine that's always on, so you open a URL on your
phone without your Mac being awake. We use **PythonAnywhere** — its free tier has
a *persistent disk*, which matters because this app stores your words in a SQLite
file (`vocab.db`). On most other free hosts that file gets wiped on every restart.

## One-time setup

1. **Make an account** at https://www.pythonanywhere.com (Free "Beginner" plan).

2. **Open a Bash console** (Dashboard → "New console" → Bash) and clone the repo:
   ```bash
   git clone https://github.com/Rorath/Vocab-Notes.git
   ```

3. **Create a virtualenv and install deps:**
   ```bash
   cd Vocab-Notes
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create the web app:** Web tab → "Add a new web app" → *Manual configuration*
   → pick the same Python version you used above (e.g. 3.10).

5. **Point it at the code.** On the Web tab set:
   - **Source code:** `/home/YOURUSERNAME/Vocab-Notes`
   - **Virtualenv:** `/home/YOURUSERNAME/Vocab-Notes/venv`
   - **WSGI file:** click the link to edit it, delete everything, and paste:
     ```python
     import sys
     path = "/home/YOURUSERNAME/Vocab-Notes"
     if path not in sys.path:
         sys.path.insert(0, path)
     from app import app as application
     ```
   (Replace `YOURUSERNAME` in all three.)

6. **Reload** (big green button on the Web tab). Your site is now live at
   `https://YOURUSERNAME.pythonanywhere.com` — open that on your phone. Bookmark it
   / add it to your home screen.

## Bringing your existing words along (optional)

The cloned repo does **not** include `vocab.db` (it's gitignored), so the site
starts empty. To copy your current words up: on the Web app's **Files** tab,
upload your local `vocab.db` into the `Vocab-Notes` folder, then Reload.

## Updating the site later

When you change the code on your Mac and `git push`, update the live site by
running this in a PythonAnywhere Bash console, then hitting Reload:
```bash
cd ~/Vocab-Notes && git pull
```

## Note on the two "databases"

Once deployed, the phone/live version and your Mac's local copy are *separate*
SQLite files. Words you add on your phone live on PythonAnywhere; words you add
locally stay on your Mac. They don't sync automatically.
