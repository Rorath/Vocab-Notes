// Flashcard learning mode
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
        // slight delay so text swaps while card is face-down
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
        }, card.classList.contains("flipped") ? 300 : 0);
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

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.key === "ArrowRight") document.getElementById("next-btn").click();
        else if (e.key === "ArrowLeft") document.getElementById("prev-btn").click();
        else if (e.key === " ") { e.preventDefault(); card.classList.toggle("flipped"); }
    });

    render();
});
