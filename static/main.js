// ---------- Mascot (Clau) ----------
const MASCOT_LINES = [
    "🧡",
    "🫶",
];

function mascotSay(text, ms = 2200) {
    const bubble = document.getElementById("mascot-bubble");
    if (!bubble) return;
    bubble.textContent = text;
    bubble.classList.add("show");
    clearTimeout(bubble._t);
    bubble._t = setTimeout(() => bubble.classList.remove("show"), ms);
}

function mascotCheer() {
    const m = document.getElementById("mascot");
    if (!m) return;
    m.classList.remove("cheer");
    void m.offsetWidth; // restart animation
    m.classList.add("cheer");
    mascotSay(MASCOT_LINES[Math.floor(Math.random() * MASCOT_LINES.length)]);
}

document.addEventListener("DOMContentLoaded", () => {
    const m = document.getElementById("mascot");
    if (m) {
        m.addEventListener("click", () => {
            if (m._dragged) { m._dragged = false; return; } // ignore the click that ends a drag
            mascotCheer();
        });
        m.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                mascotCheer();
            }
        });
        // greet on arrival
        setTimeout(() => mascotSay("Hi! I'm Cappy 👋", 2600), 700);
    }
});

// ---------- Dock (macOS-style magnification + bounce) ----------
document.addEventListener("DOMContentLoaded", () => {
    const dock = document.getElementById("dock");
    if (!dock) return;
    const items = [...dock.querySelectorAll(".dock-item")];
    const RANGE = 110;   // px of influence on each side of the cursor
    const MAX = 1.55;    // peak magnification

    dock.addEventListener("mousemove", (e) => {
        items.forEach((item) => {
            const r = item.getBoundingClientRect();
            const center = r.left + r.width / 2;
            const dist = Math.abs(e.clientX - center);
            let scale = 1;
            if (dist < RANGE) scale = 1 + (MAX - 1) * (1 - dist / RANGE);
            item.style.setProperty("--scale", scale.toFixed(3));
        });
    });
    dock.addEventListener("mouseleave", () => {
        items.forEach((item) => item.style.setProperty("--scale", 1));
    });

    // Keep navigation immediate; motion should never delay opening a page.
    items.forEach((item) => {
        item.addEventListener("click", () => {
            const icon = item.querySelector(".dock-icon");
            if (icon) {
                icon.classList.remove("bounce");
                void icon.offsetWidth; // restart animation
                icon.classList.add("bounce");
            }
        });
    });
});

// ---------- Theme toggle (dark neon <-> light) ----------
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;

    function refresh() {
        const isLight = document.documentElement.classList.contains("light");
        const icon = document.getElementById("theme-icon");
        const tip = document.getElementById("theme-tooltip");
        if (icon) icon.textContent = isLight ? "☀️" : "🌙";
        if (tip) tip.textContent = isLight ? "Dark mode" : "Light mode";
        btn.setAttribute("aria-label", isLight ? "Dark mode" : "Light mode");
        btn.setAttribute("aria-pressed", String(isLight));
    }
    refresh();

    btn.addEventListener("click", () => {
        const isLight = document.documentElement.classList.toggle("light");
        localStorage.setItem("theme", isLight ? "light" : "dark");
        refresh();
    });
});

// ---------- Cappy flies freely around the screen ----------
document.addEventListener("DOMContentLoaded", () => {
    const m = document.getElementById("mascot");
    if (!m) return;
    const wrap = m.querySelector(".capy-wrap");
    const margin = 8;
    const SPEED = 3.1;      // max px per frame — bump for faster flight
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    const size = { w: m.offsetWidth || 70, h: m.offsetHeight || 66 };
    let x = window.innerWidth - size.w - 28;
    let y = window.innerHeight - size.h - 60;
    let vx = -SPEED * 0.7;
    let vy = -SPEED * 0.5;
    let paused = false;
    let dragging = false;

    m.style.left = x + "px";
    m.style.top = y + "px";

    // ---- Pixel sparkle trail streaming behind Cappy ----
    const TRAIL_COLORS = ["#a855f7", "#22d3ee", "#ff9d6b", "#f472b6", "#34d399"];
    let trailX = x, trailY = y, colorI = 0;
    function spawnTrail() {
        if (reducedMotion.matches) return;
        const cx = x + size.w / 2, cy = y + size.h / 2;
        // only drop a pixel once we've moved far enough (keeps the trail even)
        if (Math.hypot(cx - trailX, cy - trailY) < 14) return;
        trailX = cx; trailY = cy;
        const p = document.createElement("div");
        p.className = "capy-trail";
        const jitter = () => (Math.random() - 0.5) * 14;
        p.style.left = (cx + jitter() - 4) + "px";
        p.style.top = (cy + jitter() - 4) + "px";
        const c = TRAIL_COLORS[colorI++ % TRAIL_COLORS.length];
        p.style.background = c;
        p.style.color = c;   // drives the box-shadow glow via currentColor
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 750);
    }

    // Pause so it's easy to click / pet
    m.addEventListener("mouseenter", () => { if (!dragging) paused = true; });
    m.addEventListener("mouseleave", () => { if (!dragging) paused = false; });
    m.addEventListener("focus", () => { paused = true; });
    m.addEventListener("blur", () => { paused = false; });

    // ---- Drag Cappy with the cursor (then "throw" him back into flight) ----
    let grabDX = 0, grabDY = 0;          // pointer offset within the sprite
    let lastX = 0, lastY = 0, lastT = 0; // for computing throw velocity
    let throwVX = 0, throwVY = 0;

    function clamp() {
        const maxX = window.innerWidth - size.w - margin;
        const maxY = window.innerHeight - size.h - margin;
        if (x < margin) x = margin; else if (x > maxX) x = maxX;
        if (y < margin) y = margin; else if (y > maxY) y = maxY;
    }

    m.addEventListener("pointerdown", (e) => {
        if (e.button !== 0) return;
        dragging = true;
        m._dragged = false;
        m.classList.add("dragging");
        m.setPointerCapture(e.pointerId);
        grabDX = e.clientX - x;
        grabDY = e.clientY - y;
        lastX = e.clientX; lastY = e.clientY; lastT = e.timeStamp;
        throwVX = throwVY = 0;
        e.preventDefault();
    });

    m.addEventListener("pointermove", (e) => {
        if (!dragging) return;
        x = e.clientX - grabDX;
        y = e.clientY - grabDY;
        clamp();
        m.style.left = x + "px";
        m.style.top = y + "px";
        // face the way we're being dragged
        if (wrap) wrap.style.setProperty("--dir", e.clientX > lastX ? -1 : 1);
        // track pointer velocity so a flick launches him
        const dt = e.timeStamp - lastT;
        if (dt > 0) {
            throwVX = (e.clientX - lastX) / dt * 16; // px per ~frame
            throwVY = (e.clientY - lastY) / dt * 16;
        }
        if (Math.abs(e.clientX - lastX) + Math.abs(e.clientY - lastY) > 3) m._dragged = true;
        lastX = e.clientX; lastY = e.clientY; lastT = e.timeStamp;
        spawnTrail();
    });

    function endDrag(e) {
        if (!dragging) return;
        dragging = false;
        m.classList.remove("dragging");
        try { m.releasePointerCapture(e.pointerId); } catch (_) {}
        // hand momentum back to the flight sim (bounded)
        const mag = Math.hypot(throwVX, throwVY);
        if (mag > 0.5) {
            const cap = Math.min(mag, SPEED * 3);
            vx = throwVX / mag * cap;
            vy = throwVY / mag * cap;
        }
        paused = m.matches(":hover"); // if released while hovering, stay put
    }
    m.addEventListener("pointerup", endDrag);
    m.addEventListener("pointercancel", endDrag);

    let frameId = null;
    let lastStep = 0;
    function schedule() {
        if (frameId === null && !document.hidden && !reducedMotion.matches) {
            frameId = requestAnimationFrame(tick);
        }
    }
    function tick(time) {
        frameId = null;
        if (document.hidden || reducedMotion.matches) return;
        if (time - lastStep < 32) { schedule(); return; }
        lastStep = time;
        if (!paused && !dragging) {
            // gentle random steering => free, wandering flight
            vx += (Math.random() - 0.5) * 0.5;
            vy += (Math.random() - 0.5) * 0.5;

            // keep the speed lively but bounded
            const mag = Math.hypot(vx, vy) || 1;
            if (mag > SPEED) { vx = vx / mag * SPEED; vy = vy / mag * SPEED; }
            else if (mag < SPEED * 0.6) { vx = vx / mag * SPEED * 0.6; vy = vy / mag * SPEED * 0.6; }

            x += vx;
            y += vy;

            const maxX = window.innerWidth - size.w - margin;
            const maxY = window.innerHeight - size.h - margin;
            if (x < margin) { x = margin; vx = Math.abs(vx); }
            if (x > maxX) { x = maxX; vx = -Math.abs(vx); }
            if (y < margin) { y = margin; vy = Math.abs(vy); }
            if (y > maxY) { y = maxY; vy = -Math.abs(vy); }

            m.style.left = x + "px";
            m.style.top = y + "px";
            // face the direction of travel (body faces left by default)
            if (wrap) wrap.style.setProperty("--dir", vx > 0 ? -1 : 1);
            spawnTrail();
        }
        schedule();
    }
    document.addEventListener("visibilitychange", schedule);
    reducedMotion.addEventListener("change", schedule);
    window.addEventListener("resize", () => {
        clamp();
        m.style.left = x + "px";
        m.style.top = y + "px";
    });
    schedule();
});

// ---------- Confetti ----------
function launchConfetti() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const colors = ["#a855f7", "#22d3ee", "#ff9d6b", "#cc785c", "#f472b6", "#34d399"];
    const count = 48;
    const fragment = document.createDocumentFragment();
    const pieces = [];
    for (let i = 0; i < count; i++) {
        const piece = document.createElement("div");
        piece.className = "confetti-piece";
        piece.style.left = Math.random() * 100 + "vw";
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = Math.random() * 0.25 + "s";
        piece.style.animationDuration = (2 + Math.random() * 1.6) + "s";
        fragment.appendChild(piece);
        pieces.push(piece);
    }
    document.body.appendChild(fragment);
    setTimeout(() => pieces.forEach((piece) => piece.remove()), 4200);
}

// ---------- Flashcard learning mode ----------
document.addEventListener("DOMContentLoaded", () => {
    if (typeof WORDS === "undefined" || WORDS.length === 0) return;

    // A word is testable only if it has something to reveal on the back —
    // an English or Chinese definition. Examples alone don't count.
    const hasDefinition = (w) =>
        ((w.english_defs || []).length > 0) || !!(w.chinese_def && w.chinese_def.trim());

    let deck = WORDS.filter(hasDefinition);
    const setAside = WORDS.filter((w) => !hasDefinition(w));
    let index = 0;

    const card = document.getElementById("flashcard");
    const wordEl = document.getElementById("card-word");
    const englishEl = document.getElementById("card-english");
    const englishBlock = document.getElementById("english-block");
    const chineseEl = document.getElementById("card-chinese");
    const sentenceEl = document.getElementById("card-sentence");
    const sentenceBlock = document.getElementById("sentence-block");
    const chineseBlock = document.getElementById("chinese-block");
    const currentIndexEl = document.getElementById("current-index");
    const totalEl = document.getElementById("total");
    const saveStatus = document.getElementById("save-status");

    // Show the words that were pulled out of the deck (no definition yet).
    const asideEl = document.getElementById("set-aside");
    const asideList = document.getElementById("set-aside-list");
    if (asideEl && asideList && setAside.length) {
        const countEl = document.getElementById("set-aside-count");
        if (countEl) countEl.textContent = setAside.length;
        setAside.forEach((w) => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = "/edit/" + w.id;
            a.textContent = w.word;
            li.appendChild(a);
            asideList.appendChild(li);
        });
        asideEl.hidden = false;
    }

    // If every word was set aside, there's nothing to flip through.
    if (deck.length === 0) {
        const emptyEl = document.getElementById("deck-empty");
        if (emptyEl) emptyEl.hidden = false;
        if (card) card.hidden = true;
        const controls = document.querySelector(".learn-controls");
        if (controls) controls.hidden = true;
        if (totalEl) totalEl.textContent = "0";
        if (currentIndexEl) currentIndexEl.textContent = "0";
        return;
    }

    if (totalEl) totalEl.textContent = deck.length;

    function render() {
        const w = deck[index];
        card.classList.remove("flipped");
        card.setAttribute("aria-pressed", "false");
        card.setAttribute("aria-label", "Reveal definition for " + w.word);
        wordEl.textContent = w.word;
        const defs = w.english_defs || [];
        englishEl.textContent = defs.join("\n");
        englishBlock.style.display = defs.length ? "block" : "none";
        chineseEl.textContent = w.chinese_def || "";
        chineseBlock.style.display = w.chinese_def ? "block" : "none";
        const examples = w.examples || [];
        sentenceEl.textContent = examples.join("\n");
        sentenceBlock.style.display = examples.length ? "block" : "none";
        currentIndexEl.textContent = index + 1;
    }

    function flipCard() {
        const flipped = card.classList.toggle("flipped");
        card.setAttribute("aria-pressed", String(flipped));
        card.setAttribute("aria-label", (flipped ? "Hide" : "Reveal") + " definition for " + deck[index].word);
    }
    card.addEventListener("click", flipCard);

    // ---- Weighted selection: less-familiar words surface more often --------
    const famOf = (w) => (typeof w.familiarity === "number" ? w.familiarity : 0);
    // Weight falls as familiarity climbs; a missed word (negative score) is many
    // times more likely to be drawn than a well-known one.
    const weightOf = (w) => Math.max(1, 7 - famOf(w));

    function weightedIndex(exclude) {
        if (deck.length <= 1) return 0;
        let total = 0;
        const weights = deck.map((w, i) => {
            const wt = i === exclude ? 0 : weightOf(w);
            total += wt;
            return wt;
        });
        let r = Math.random() * total;
        for (let i = 0; i < deck.length; i++) {
            r -= weights[i];
            if (r < 0) return i;
        }
        return (exclude + 1) % deck.length;
    }

    const history = [];
    function goTo(next) { history.push(index); index = next; render(); }
    function advance() { goTo(weightedIndex(index)); }

    // Record how an answer went and refresh the daily-goal bar from the reply.
    let answering = false;
    const knownBtn = document.getElementById("known-btn");
    const idkBtn = document.getElementById("idk-btn");
    const answerControls = [knownBtn, idkBtn, document.getElementById("next-btn"), document.getElementById("prev-btn"), document.getElementById("shuffle-btn")];

    async function postResult(known) {
        if (answering) return;
        answering = true;
        answerControls.forEach((button) => { button.disabled = true; });
        saveStatus.textContent = "Saving answer…";
        const w = deck[index];
        try {
            const response = await fetch("/api/result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: w.id, known }),
            });
            if (!response.ok) throw new Error("Save failed");
            const data = await response.json();
            w.familiarity = data.familiarity;
            DAILY.today = data.today;
            DAILY.goal = data.goal;
            renderGoal();
            saveStatus.textContent = "";
            if (known) {
                launchConfetti();
                mascotCheer();
                if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                    await new Promise((resolve) => setTimeout(resolve, 450));
                }
            } else {
                mascotSay("No worries — I'll bring this one back around.");
            }
            advance();
        } catch (_) {
            saveStatus.textContent = "Couldn't save your answer. Please try again.";
        } finally {
            answering = false;
            answerControls.forEach((button) => { button.disabled = false; });
        }
    }

    document.getElementById("next-btn").addEventListener("click", advance);

    document.getElementById("prev-btn").addEventListener("click", () => {
        if (history.length) { index = history.pop(); render(); }
        else { index = (index - 1 + deck.length) % deck.length; render(); }
    });

    document.getElementById("shuffle-btn").addEventListener("click", () => {
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        history.length = 0;
        index = weightedIndex(-1);
        render();
    });

    if (knownBtn) {
        knownBtn.addEventListener("click", () => postResult(true));
    }

    if (idkBtn) {
        idkBtn.addEventListener("click", () => postResult(false));
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.target === card && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            flipCard();
            return;
        }
        if (e.target.closest("input, textarea, select, button, a, [role=button], [contenteditable]")) return;
        if (e.key === "ArrowRight") document.getElementById("next-btn").click();
        else if (e.key === "ArrowLeft") document.getElementById("prev-btn").click();
        else if (e.key === " ") { e.preventDefault(); flipCard(); }
        else if (e.key === "Enter" && knownBtn) knownBtn.click();
        else if ((e.key === "x" || e.key === "X") && idkBtn) idkBtn.click();
    });

    // ---- Daily goal bar ----------------------------------------------------
    const goalWrap = document.getElementById("daily-goal");
    const goalFill = document.getElementById("goal-fill");
    const goalText = document.getElementById("goal-text");
    const goalInput = document.getElementById("goal-input");
    const goalEdit = document.getElementById("goal-edit");

    function renderGoal() {
        if (!goalWrap) return;
        const today = DAILY.today || 0;
        const goal = DAILY.goal || 0;
        if (goal > 0) {
            const pct = Math.min(100, Math.round((today / goal) * 100));
            goalFill.style.width = pct + "%";
            goalWrap.classList.toggle("goal-done", today >= goal);
            goalText.textContent = today >= goal
                ? `🎉 Daily goal reached — ${today}/${goal} reviews today`
                : `${today} / ${goal} reviews today`;
            goalEdit.textContent = "Edit";
        } else {
            goalFill.style.width = "0%";
            goalWrap.classList.remove("goal-done");
            goalText.textContent = today
                ? `${today} reviews today · no goal set`
                : "No daily goal set";
            goalEdit.textContent = "Set daily goal";
        }
    }

    function saveGoal() {
        if (!goalInput || goalInput.hidden) return;
        const val = Math.max(0, parseInt(goalInput.value, 10) || 0);
        goalInput.hidden = true;
        saveStatus.textContent = "";
        fetch("/api/goal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ goal: val }),
        })
            .then((r) => {
                if (!r.ok) throw new Error("Save failed");
                return r.json();
            })
            .then((data) => {
                DAILY.goal = data.goal;
                DAILY.today = data.today;
                renderGoal();
            })
            .catch(() => { saveStatus.textContent = "Couldn't save your goal. Please try again."; });
    }

    if (goalEdit && goalInput) {
        goalEdit.addEventListener("click", () => {
            goalInput.hidden = false;
            goalInput.value = DAILY.goal || "";
            goalInput.focus();
        });
        goalInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") { e.preventDefault(); saveGoal(); }
        });
        goalInput.addEventListener("blur", saveGoal);
    }

    renderGoal();
    render();
});

// ---- Word cards: cross-fade through multiple examples every 10s ----
document.addEventListener("DOMContentLoaded", () => {
    const rotators = [];
    document.querySelectorAll(".example-rotator.is-rotating").forEach((rotator) => {
        const stack = rotator.querySelector(".example-stack");
        const items = [...rotator.querySelectorAll(".example-item")];
        const dots = [...rotator.querySelectorAll(".example-dot")];
        if (items.length < 2) return;

        let i = 0;
        const fit = () => { stack.style.height = items[i].offsetHeight + "px"; };
        fit();
        rotators.push({ fit, advance: () => {
            const prev = i;
            i = (i + 1) % items.length;
            items[prev].classList.remove("active");
            items[i].classList.add("active");
            if (dots.length) {
                dots[prev].classList.remove("active");
                dots[i].classList.add("active");
            }
            stack.style.height = items[i].offsetHeight + "px";
        }});
    });
    if (!rotators.length) return;
    window.addEventListener("resize", () => rotators.forEach(({ fit }) => fit()));
    setInterval(() => {
        if (document.hidden || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        rotators.forEach(({ advance }) => advance());
    }, 10000);
});

// ---- Word grid: multi-select words and move them into one group ----
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("select-toggle");
    const bar = document.getElementById("bulk-form");
    if (!toggle || !bar) return;

    const checks = [...document.querySelectorAll(".card-check")];
    const countEl = document.getElementById("bulk-n");
    const applyBtn = document.getElementById("bulk-apply");
    const cancelBtn = document.getElementById("bulk-cancel");
    const allBtn = document.getElementById("bulk-all");

    const selected = () => checks.filter((c) => c.checked);

    function refresh() {
        const n = selected().length;
        countEl.textContent = n;
        applyBtn.disabled = n === 0;
        allBtn.textContent = n === checks.length ? "Clear all" : "Select all";
    }

    function setMode(on) {
        document.body.classList.toggle("selecting", on);
        toggle.classList.toggle("active", on);
        toggle.textContent = on ? "✕ Done" : "☑︎ Select";
        if (!on) {
            checks.forEach((c) => { c.checked = false; });
            checks.forEach((c) => c.closest("[data-word-card]").classList.remove("is-selected"));
            refresh();
        }
    }

    toggle.addEventListener("click", () => setMode(!document.body.classList.contains("selecting")));
    cancelBtn.addEventListener("click", () => setMode(false));

    allBtn.addEventListener("click", () => {
        const target = selected().length !== checks.length;
        checks.forEach((c) => {
            c.checked = target;
            c.closest("[data-word-card]").classList.toggle("is-selected", target);
        });
        refresh();
    });

    // In select mode, clicking anywhere on a card toggles its checkbox
    document.querySelectorAll("[data-word-card]").forEach((card) => {
        card.addEventListener("click", (e) => {
            if (!document.body.classList.contains("selecting")) return;
            if (e.target.closest("a, button, .actions")) return; // let real controls work
            const check = card.querySelector(".card-check");
            if (!check) return;
            if (e.target !== check) check.checked = !check.checked;
            card.classList.toggle("is-selected", check.checked);
            refresh();
        });
    });

    checks.forEach((c) => c.addEventListener("change", () => {
        c.closest("[data-word-card]").classList.toggle("is-selected", c.checked);
        refresh();
    }));

    refresh();
});

// ---- Add/Edit form: dynamic multi-input rows (definitions & examples) ----
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn-add-example[data-add]").forEach((addBtn) => {
        const inputs = document.getElementById(addBtn.dataset.add);
        if (!inputs) return;
        const name = inputs.dataset.name;
        const placeholder = inputs.dataset.placeholder || "";

        const makeRow = (value = "") => {
            const row = document.createElement("div");
            row.className = "example-input-row";
            const ta = document.createElement("textarea");
            ta.name = name;
            ta.rows = 2;
            ta.placeholder = placeholder;
            ta.value = value;
            const rm = document.createElement("button");
            rm.type = "button";
            rm.className = "btn-remove-example";
            rm.setAttribute("aria-label", "Remove");
            rm.textContent = "✕";
            row.append(ta, rm);
            return row;
        };

        addBtn.addEventListener("click", () => {
            const row = makeRow();
            inputs.appendChild(row);
            row.querySelector("textarea").focus();
        });

        inputs.addEventListener("click", (e) => {
            if (!e.target.classList.contains("btn-remove-example")) return;
            const rows = inputs.querySelectorAll(".example-input-row");
            if (rows.length > 1) {
                e.target.closest(".example-input-row").remove();
            } else {
                e.target.closest(".example-input-row").querySelector("textarea").value = "";
            }
        });
    });
});
