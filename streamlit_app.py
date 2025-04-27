import streamlit as st
import pandas as pd
import os
import random
import shutil
import datetime
from pathlib import Path
from openai import OpenAI

# ========== Config ==========
BASE_DIR = Path(__file__).resolve().parent           # スクリプトと同じディレクトリ
CSV_PATH = BASE_DIR / "wordlist.csv"                # 絶対パスで管理
CLIENT = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ========== Helpers ==========

def backup_csv(path: Path) -> None:
    """上書き前にバックアップコピーを残す"""
    if path.exists():
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(path, path.with_suffix(f".bak.{ts}"))


def load_words() -> list[str]:
    """CSV から単語リストを読み込む。存在しなければ空リスト"""
    if CSV_PATH.exists():
        try:
            df = pd.read_csv(CSV_PATH, header=None, names=["word"])
            return df["word"].dropna().tolist()
        except Exception as e:
            st.error(f"CSV 読み込み失敗: {e}")
    return []


def save_words(words: list[str]) -> None:
    """単語リストを CSV に保存 (空リストは保存しない)"""
    if not words:
        st.warning("空リストは保存しませんでした。")
        return
    backup_csv(CSV_PATH)
    pd.DataFrame(words, columns=["word"]).to_csv(CSV_PATH, index=False, header=False)


def generate_dialogue(words: list[str]) -> str:
    prompt = (
        "Create a short and funny conversation between a playful man named Tom and a cute, sociable girl named Lisa. "
        "Both are witty and often come up with clever remarks. "
        "Sometimes, Lisa shows off her beauty and big breasts, teasing people with playful, naughty jokes. "
        "The conversation must naturally include these word(s) exactly once each: "
        f"{', '.join(words)}. "
        "Either Tom or Lisa should start the conversation randomly. "
        "Make it friendly and humorous, 4-6 lines long. The topic can be anything. "
        "First output the English conversation, then provide a fluent Japanese translation right below it, "
        "and finally give a simple definition for every listed word in Japanese. "
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
st.set_page_config(page_title="Word Fun App", page_icon="🗨️", layout="centered")

st.title("Word Learning App 🗨️")

# CSV の保存場所をデバッグ表示 (ユーザー確認用)
st.caption(f"CSV path: {CSV_PATH}")

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

    if not words_total:
        st.warning("まず単語を登録してください。")
    else:
        mode = st.radio("Select mode", ["🎲 Random 3 words", "📝 Pick my own"], horizontal=True, key="select_mode")

        # ---------- Mode 1: Random 3 words ----------
        if mode == "🎲 Random 3 words":
            if len(words_total) < 3:
                st.warning("3 語以上登録されていません。")
            else:
                if st.button("Select & Generate", key="random_generate"):
                    selected = random.sample(words_total, 3)
                    st.write("### Selected Words", ", ".join(selected))
                    result = generate_dialogue(selected)
                    st.markdown(result)

        # ---------- Mode 2: User picks any number ----------
        else:
            picked = st.multiselect("Choose as many words as you like (min 1)", words_total, key="picked_words")
            if st.button("Generate with selected words", key="custom_generate"):
                if not picked:
                    st.warning("少なくとも 1 語選択してください。")
                else:
                    st.write("### Selected Words", ", ".join(picked))
                    result = generate_dialogue(picked)
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
