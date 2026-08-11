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
        setTimeout(() => mascotSay("Hi! I'm Clau 👋", 2600), 700);
    }
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
    const chineseEl = document.getElementById("card-chinese");
    const sentenceEl = document.getElementById("card-sentence");
    const sentenceBlock = document.getElementById("sentence-block");
    const currentIndexEl = document.getElementById("current-index");

    function render() {
        const w = deck[index];
        card.classList.remove("flipped");
        setTimeout(() => {
            wordEl.textContent = w.word;
            englishEl.textContent = w.english_def;
            chineseEl.textContent = w.chinese_def;
            if (w.sentence) {
                sentenceEl.textContent = w.sentence;
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
