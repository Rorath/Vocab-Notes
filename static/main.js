// ---------- Mascot (Clau) ----------
const MASCOT_LINES = [
    "You've got this! 🧡",
    "Keep going, superstar!",
    "One word at a time ✨",
    "I'm proud of you!",
    "Nice work! 🎉",
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
            mascotCheer();
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

    // Bounce on click; delay navigation so the animation is visible
    items.forEach((item) => {
        item.addEventListener("click", (e) => {
            const icon = item.querySelector(".dock-icon");
            if (icon) {
                icon.classList.remove("bounce");
                void icon.offsetWidth; // restart animation
                icon.classList.add("bounce");
            }
            const href = item.getAttribute("href");
            if (href) {
                e.preventDefault();
                setTimeout(() => { window.location.href = href; }, 470);
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

    const size = { w: m.offsetWidth || 70, h: m.offsetHeight || 66 };
    let x = window.innerWidth - size.w - 28;
    let y = window.innerHeight - size.h - 60;
    let vx = -SPEED * 0.7;
    let vy = -SPEED * 0.5;
    let paused = false;

    m.style.left = x + "px";
    m.style.top = y + "px";

    // Pause so it's easy to click / pet
    m.addEventListener("mouseenter", () => { paused = true; });
    m.addEventListener("mouseleave", () => { paused = false; });

    function tick() {
        if (!paused) {
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
        }
        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
});

// ---------- Confetti ----------
function launchConfetti() {
    const colors = ["#a855f7", "#22d3ee", "#ff9d6b", "#cc785c", "#f472b6", "#34d399"];
    const count = 90;
    for (let i = 0; i < count; i++) {
        const piece = document.createElement("div");
        piece.className = "confetti-piece";
        piece.style.left = Math.random() * 100 + "vw";
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = Math.random() * 0.25 + "s";
        piece.style.animationDuration = (2 + Math.random() * 1.6) + "s";
        document.body.appendChild(piece);
        setTimeout(() => piece.remove(), 4200);
    }
}

// ---------- Flashcard learning mode ----------
document.addEventListener("DOMContentLoaded", () => {
    if (typeof WORDS === "undefined" || WORDS.length === 0) return;

    let deck = [...WORDS];
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

    function render() {
        const w = deck[index];
        card.classList.remove("flipped");
        setTimeout(() => {
            wordEl.textContent = w.word;
            const defs = w.english_defs || [];
            if (defs.length) {
                englishEl.textContent = defs.join("\n");
                englishBlock.style.display = "block";
            } else {
                englishBlock.style.display = "none";
            }
            if (w.chinese_def) {
                chineseEl.textContent = w.chinese_def;
                chineseBlock.style.display = "block";
            } else {
                chineseBlock.style.display = "none";
            }
            const examples = w.examples || [];
            if (examples.length) {
                sentenceEl.textContent = examples.join("\n");
                sentenceBlock.style.display = "block";
            } else {
                sentenceBlock.style.display = "none";
            }
            currentIndexEl.textContent = index + 1;
        }, card.classList.contains("flipped") ? 350 : 0);
    }

    card.addEventListener("click", () => card.classList.toggle("flipped"));

    document.getElementById("next-btn").addEventListener("click", () => {
        index = (index + 1) % deck.length;
        render();
    });

    document.getElementById("prev-btn").addEventListener("click", () => {
        index = (index - 1 + deck.length) % deck.length;
        render();
    });

    document.getElementById("shuffle-btn").addEventListener("click", () => {
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        index = 0;
        render();
    });

    const knownBtn = document.getElementById("known-btn");
    if (knownBtn) {
        knownBtn.addEventListener("click", () => {
            launchConfetti();
            mascotCheer();
            setTimeout(() => {
                index = (index + 1) % deck.length;
                render();
            }, 450);
        });
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.key === "ArrowRight") document.getElementById("next-btn").click();
        else if (e.key === "ArrowLeft") document.getElementById("prev-btn").click();
        else if (e.key === " ") { e.preventDefault(); card.classList.toggle("flipped"); }
        else if (e.key === "Enter" && knownBtn) knownBtn.click();
    });

    render();
});

// ---- Word cards: cross-fade through multiple examples every 10s ----
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".example-rotator.is-rotating").forEach((rotator) => {
        const stack = rotator.querySelector(".example-stack");
        const items = [...rotator.querySelectorAll(".example-item")];
        const dots = [...rotator.querySelectorAll(".example-dot")];
        if (items.length < 2) return;

        let i = 0;
        const fit = () => { stack.style.height = items[i].offsetHeight + "px"; };
        fit();
        window.addEventListener("resize", fit);

        setInterval(() => {
            const prev = i;
            i = (i + 1) % items.length;
            items[prev].classList.remove("active");
            items[i].classList.add("active");
            if (dots.length) {
                dots[prev].classList.remove("active");
                dots[i].classList.add("active");
            }
            stack.style.height = items[i].offsetHeight + "px";
        }, 10000);
    });
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
