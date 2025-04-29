import streamlit as st
import pandas as pd
import random
import shutil
import datetime
from pathlib import Path
from openai import OpenAI

# ========== Config ==========
BASE_DIR = Path(__file__).resolve().parent           # スクリプトのディレクトリ
CSV_PATH = BASE_DIR / "wordlist.csv"                # 単語 CSV
CLIENT = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ========== Helpers ==========

# def backup_csv(path: Path) -> None:
#     """CSV を上書きする前に日時付きバックアップを作成"""
#     if path.exists():
#         ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#         shutil.copy(path, path.with_suffix(f".bak.{ts}"))


def load_words() -> list[str]:
    """CSV から単語リストを読み込む (無い場合は空リスト)"""
    if CSV_PATH.exists():
        try:
            return pd.read_csv(CSV_PATH, header=None)[0].dropna().tolist()
        except Exception as e:
            st.error(f"CSV 読み込み失敗: {e}")
    return []


def save_words(words: list[str]) -> None:
    """単語リストを CSV に保存 (空リストの場合はスキップ)"""
    if not words:
        st.warning("空リストは保存されませんでした。")
        return
    backup_csv(CSV_PATH)
    pd.Series(words).to_csv(CSV_PATH, index=False, header=False)


def generate_dialogue(words: list[str]) -> str:
    """選択された単語を必ず 1 回ずつ含む Tom & Lisa の会話を生成"""
    starter = random.choice(["Tom", "Lisa"])
    prompt = (
        "Create a short and funny conversation between a playful man named Tom and a cute, sociable girl named Lisa. "
        "Both are friends who work at the same company. Tom are witty and often come up with clever remarks. "
        "Tom is an process engineer at an EPC engineering company."
        "Sometimes, Lisa complains or teases people at work with playful, naughty jokes. "
        "The conversation must naturally include these word(s) exactly once each: "
        f"{', '.join(words)}. "
        f"The conversation MUST start with {starter}: "
        "The conversation must include one expression or word that an English learner at the level between C1 and C2 should know."
        "Make it friendly and humorous, 4-6 lines long. The topic can be anything. "
        "First, output the English conversation, then provide a fluent Japanese translation right below it."
        "and finally give a simple definition for every listed word and the expression (or word) in Japanese. "
        "Clearly separate the English conversation, Japanese translation, and word meanings."
    )

    try:
        res = CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative writer specializing in funny dialogues."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"会話生成エラー: {e}")
        return "会話の生成に失敗しました。"

# ========== UI ==========
st.set_page_config(page_title="Word Learning App", page_icon="🗨️", layout="centered")

st.title("Word Learning App 🗨️")

tab_dialogue, tab_wordlist = st.tabs(["💬 Dialogue Creation", "📚 Word List"])

# ---------------- Dialogue Creation Tab -----------------
with tab_dialogue:
    st.subheader("Generate a Dialogue 🗣️")

    # --- New word registration ---
    with st.expander("➕  Add / Register a new word"):
        new_word = st.text_input("Enter a new English word", key="new_word_input")
        if st.button("Register Word", key="register_word") and new_word.strip():
            words_all = load_words() + [new_word.strip()]
            save_words(words_all)
            st.success(f"'{new_word}' を登録しました！")
            st.rerun()

    words_total = load_words()
    st.caption("**Registered words:** " + (", ".join(words_total) if words_total else "None yet."))

    if words_total:
        mode = st.radio("Select mode", ["🎲 Random 3 words", "📝 Pick my own"], horizontal=True)

        if mode == "🎲 Random 3 words":
            if len(words_total) < 3:
                st.warning("3 語以上登録されていません。")
            elif st.button("Select & Generate"):
                selected = random.sample(words_total, 3)
                st.write("### Selected Words", ", ".join(selected))
                st.markdown(generate_dialogue(selected))
        else:
            picked = st.multiselect("Choose as many words as you like (min 1)", words_total)
            if st.button("Generate with selected words"):
                if picked:
                    st.write("### Selected Words", ", ".join(picked))
                    st.markdown(generate_dialogue(picked))
                else:
                    st.warning("少なくとも 1 語選択してください。")
    else:
        st.warning("まず単語を登録してください。")

# ---------------- Word List Tab -----------------
with tab_wordlist:
    st.subheader("Manage Your Word List 📚")

    words = load_words()
    if words:
        # Download current CSV
        with st.expander("⬇️ Download / Backup current CSV"):
            with open(CSV_PATH, "rb") as f:
                st.download_button("💾 Download current wordlist.csv", f, "wordlist.csv", "text/csv")

        # Display and delete words
        for idx, w in enumerate(words):
            col1, col2 = st.columns([4, 1])
            col1.write(f"- {w}")
            if col2.button("🗑️", key=f"del_{idx}"):
                words.pop(idx)
                save_words(words)
                st.rerun()

        st.divider()
    else:
        st.info("まだ単語が登録されていません。Dialogue Creation タブで追加してください。")

    # Add word from this tab
    new_word2 = st.text_input("Add another word", key="new_word_in_list")
    if st.button("Add", key="add_in_list") and new_word2.strip():
        save_words(words + [new_word2.strip()])
        st.success(f"'{new_word2}' を追加しました！")
        st.rerun()
