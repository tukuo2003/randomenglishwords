import streamlit as st
import pandas as pd
import random
import datetime, shutil
from pathlib import Path
from openai import OpenAI

# ===== Config =========================================================
BASE_DIR  = Path(__file__).resolve().parent
CSV_PATH  = BASE_DIR / "wordlist.csv"
CLIENT    = OpenAI(api_key=st.secrets["openai"]["api_key"])

ADVANCED_WORDS = [
    "conundrum", "albeit", "ubiquitous", "meticulous", "unequivocal",
    "transient", "juxtapose", "relinquish", "scrutinize", "innate",
]

# ===== Helpers ========================================================
def backup_csv(path: Path) -> None:
    if path.exists():
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(path, path.with_suffix(f".bak.{ts}"))

def load_words() -> list[str]:
    if CSV_PATH.exists():
        try:
            return pd.read_csv(CSV_PATH, header=None)[0].dropna().tolist()
        except Exception as e:
            st.error(f"CSV 読み込み失敗: {e}")
    return []

def save_words(words: list[str]) -> None:
    if not words:
        return
    backup_csv(CSV_PATH)
    pd.Series(words).to_csv(CSV_PATH, index=False, header=False)

def generate_dialogue(base_words: list[str]) -> str:
    """選ばれた語 + ランダム C1/C2 語 1 つを入れた会話を返す"""
    advanced = random.choice([w for w in ADVANCED_WORDS if w not in base_words])
    words    = base_words + [advanced]
    starter  = random.choice(["Tom", "Lisa"])

    prompt = (
        "Create a short and funny conversation between a playful man named Tom and "
        "a cute, sociable girl named Lisa who work at the same EPC engineering company. "
        "Lisa loves talking about gossip or teasing Tom's boss with playful, naughty jokes.\n\n"
        f"The conversation MUST start with {starter}: \n"
        "• include EACH of these word(s) exactly once: " + ", ".join(words) + "\n"
        "• length: 4–6 lines, friendly & humorous\n\n"
        "Do not talk about coffee."
        "After the English conversation, add:\n"
        "1) a fluent Japanese translation\n"
        "2) simple Japanese definitions of every listed word (including the C1/C2 word)\n"
        "Clearly separate the three sections."
    )

    res = CLIENT.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a creative writer specializing in funny dialogues."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=650,
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()

# ===== Streamlit UI ===================================================
st.set_page_config("Word Learning App", "🗨️", layout="centered")
st.title("Word Learning App 🗨️")

# --- 初期化 ---
if "selected_words" not in st.session_state:
    st.session_state.selected_words = []
if "dialogue" not in st.session_state:
    st.session_state.dialogue = ""

tab_dialogue, tab_wordlist = st.tabs(["💬 Dialogue", "📚 Word List"])

# ---------------- Dialogue Tab ----------------
with tab_dialogue:
    st.subheader("1️⃣  Select Words")

    words_total = load_words()
    st.caption("**Registered words:** " + (", ".join(words_total) if words_total else "None yet."))

    colA, colB = st.columns(2)

    # --- ランダム抽選 ---
    with colA:
        st.write("### 🎲 Random 3 words")
        if len(words_total) < 3:
            st.info("3語以上登録すると使えます。")
        elif st.button("Pick Random"):
            st.session_state.selected_words = random.sample(words_total, 3)

    # --- 手動選択 ---
    with colB:
        st.write("### 📝 Pick my own")
        picked = st.multiselect(
            "Choose any number",
            options=words_total,
            default=st.session_state.selected_words,  # 直前の選択を保持
        )
        if st.button("Set Selection"):
            st.session_state.selected_words = picked

    # --- 現在の選択状況 ---
    if st.session_state.selected_words:
        st.success("**Current selection:** " + ", ".join(st.session_state.selected_words))
    else:
        st.warning("まだ単語が選ばれていません。")

    st.divider()
    st.subheader("2️⃣  Generate Dialogue")

    if st.button("🚀 Generate"):
        if st.session_state.selected_words:
            st.session_state.dialogue = generate_dialogue(st.session_state.selected_words)
        else:
            st.warning("まず単語を選択してください。")

    # --- 生成結果の表示（セッションに保持） ---
    if st.session_state.dialogue:
        st.markdown("### ✨ Dialogue")
        st.markdown(st.session_state.dialogue)

    # --- 新単語登録（会話を消さない） ---
    with st.expander("➕  Add / Register a new word"):
        new_word = st.text_input("Enter a new English word", key="new_word_input")
        if st.button("Register Word", key="register_word") and new_word.strip():
            save_words(list(dict.fromkeys(load_words() + [new_word.strip()])))  # 重複排除
            st.success(f"'{new_word}' を登録しました！")
            st.rerun()

# ---------------- Word List Tab --------------
with tab_wordlist:
    st.subheader("📜 Current Word List")

    words = load_words()
    if words:
        # ダウンロード
        with st.expander("⬇️ Download / Backup current CSV"):
            with open(CSV_PATH, "rb") as f:
                st.download_button("💾 Download wordlist.csv", f, "wordlist.csv", "text/csv")

        # 表示と削除
        for idx, w in enumerate(words):
            col1, col2 = st.columns([5, 1])
            col1.write(f"- {w}")
            if col2.button("🗑️", key=f"del_{idx}"):
                words.pop(idx)
                save_words(words)
                st.rerun()
    else:
        st.info("まだ単語が登録されていません。Dialogue タブで追加してください。")

    # 追加入力
    st.divider()
    new_word2 = st.text_input("Add another word", key="new_word_in_list")
    if st.button("Add", key="add_in_list") and new_word2.strip():
        save_words(list(dict.fromkeys(words + [new_word2.strip()])))
        st.success(f"'{new_word2}' を追加しました！")
        st.rerun()
