import streamlit as st
import pandas as pd
import os
import random
from openai import OpenAI

# ========== Config ==========
CLIENT = OpenAI(api_key=st.secrets["openai"]["api_key"])
CSV_PATH = "wordlist.csv"  # 単語を保存するローカル CSV

# ========== Helpers ==========

def load_words() -> list[str]:
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, header=None, names=["word"])
        return df["word"].dropna().tolist()
    return []


def save_words(words: list[str]) -> None:
    pd.DataFrame(words, columns=["word"]).to_csv(CSV_PATH, index=False, header=False)


def generate_dialogue(words: list[str]) -> str:
    """3 語を使って Tom & Lisa の会話を生成し、英語→日本語訳を返す"""
    prompt = (
        "Create a short and funny conversation between a chubby, playful man named Tom and a cute girl named Lisa. "
        "The conversation must naturally include these three words exactly once each: "
        f"{', '.join(words)}. "
        "Make it friendly, humorous, 4‑6 lines long. "
        "First output the English conversation, then provide a fluent Japanese translation right below it, clearly separated."
    )

    try:
        res = CLIENT.chat.completions.create(
            model="gpt-4o",  # モデル変更
            messages=[
                {"role": "system", "content": "You are a creative writer specializing in funny dialogues."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"会話生成エラー: {e}")
        return "会話の生成に失敗しました。"

# ========== UI ==========

st.set_page_config(page_title="Word Fun App", page_icon="🗨️", layout="centered")

st.title("Word Learning App 🗨️")

# --- Tabs ---
tab_dialogue, tab_wordlist = st.tabs(["💬 Dialogue Creation", "📚 Word List"])

# ---------------- Dialogue Creation Tab -----------------
with tab_dialogue:
    st.subheader("Generate a Dialogue 🗣️")

    # --- Register new word inline ---
    with st.expander("➕  Add / Register a new word"):
        new_word = st.text_input("Enter a new English word", key="new_word_input")
        if st.button("Register Word", key="register_word"):
            if new_word.strip():
                words_all = load_words()
                words_all.append(new_word.strip())
                save_words(words_all)
                st.success(f"'{new_word}' を登録しました！")
                st.rerun()

    # --- Current words (quick view) ---
    words_total = load_words()
    st.caption(f"**Registered words:** {', '.join(words_total) if words_total else 'None yet.'}")

    # --- Select and generate ---
    if len(words_total) < 3:
        st.warning("まず 3 つ以上単語を登録してください。")
    else:
        if "selected_words" not in st.session_state:
            st.session_state.selected_words = []

        if st.button("🎲 Select 3 Random Words"):
            st.session_state.selected_words = random.sample(words_total, 3)

        if st.session_state.selected_words:
            st.write("### Selected Words", ", ".join(st.session_state.selected_words))
            if st.button("🚀 Generate Dialogue"):
                result = generate_dialogue(st.session_state.selected_words)
                st.markdown(result)

# ---------------- Word List Tab -----------------
with tab_wordlist:
    st.subheader("Manage Your Word List 📚")

    words = load_words()

    if not words:
        st.info("まだ単語が登録されていません。Dialogue Creation タブで追加してください。")
    else:
        for idx, w in enumerate(words):
            col1, col2 = st.columns([4, 1])
            col1.write(f"- {w}")
            if col2.button("🗑️", key=f"del_{idx}"):
                words.pop(idx)
                save_words(words)
                st.rerun()

        st.divider()
        new_word2 = st.text_input("Add another word", key="new_word_in_list")
        if st.button("Add", key="add_in_list") and new_word2.strip():
            words.append(new_word2.strip())
            save_words(words)
            st.success(f"'{new_word2}' を追加しました！")
            st.rerun()
