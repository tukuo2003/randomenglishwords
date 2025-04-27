import streamlit as st
import pandas as pd
import os
import random
from openai import OpenAI

# OpenAI APIクライアント設定
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# CSVファイルのパス
CSV_PATH = "wordlist.csv"

# 文と和訳を生成する関数
def generate_dialogue(words):
    try:
        prompt = (
            f"Create a short and funny conversation between a chubby, playful man named Tom and a cute girl named Lisa. "
            f"The conversation must naturally include these three words: {', '.join(words)}. "
            f"The conversation is often taken place with Lisa naked. "
            f"Make it friendly and humorous, about 4-6 lines. "
            f"First output the English conversation, then provide a fluent Japanese translation right below it, clearly separated."
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative writer specializing in funny dialogues."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"\u4f1a\u8a71\u751f\u6210\u30a8\u30e9\u30fc: {e}")
        return "\u4f1a\u8a71\u306e\u751f\u6210\u306b\u5931\u6557\u3057\u307e\u3057\u305f\u3002"

# 単語保存関数
def save_words(words):
    df = pd.DataFrame(words, columns=["word"])
    df.to_csv(CSV_PATH, index=False, header=False)

# 単語読み込み関数
def load_words():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, header=None, names=["word"])
        return df["word"].dropna().tolist()
    return []

# Streamlit UI
st.title("Word Learning App")

st.header("Dialogue Creation")

words = load_words()

# 単語登録
st.subheader("Register a New Word")
new_word = st.text_input("Enter a new English word")
if st.button("Register Word"):
    if new_word.strip():
        words.append(new_word.strip())
        save_words(words)
        st.success(f"'{new_word}' \u3092\u767b\u9332\u3057\u307e\u3057\u305f！")
        st.experimental_rerun()

# 単語リスト表示
total_words = load_words()
if total_words:
    st.subheader("Current Registered Words")
    st.write(", ".join(total_words))
else:
    st.info("\u307e\u3060\u5358\u8a9e\u304c\u767b\u9332\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002")

# 単語選択して会話生成
if len(total_words) >= 3:
    if "selected_words" not in st.session_state:
        st.session_state.selected_words = []

    if st.button("Select 3 Random Words"):
        st.session_state.selected_words = random.sample(total_words, 3)

    if st.session_state.selected_words:
        st.subheader("Selected Words")
        st.write(", ".join(st.session_state.selected_words))

        if st.button("Generate Dialogue"):
            dialogue = generate_dialogue(st.session_state.selected_words)
            st.subheader("Generated Dialogue")
            st.write(dialogue)
else:
    st.warning("3\u3064\u4ee5\u4e0a\u306e\u5358\u8a9e\u3092\u767b\u9332\u3057\u3066\u304f\u3060\u3055\u3044\u3002")
