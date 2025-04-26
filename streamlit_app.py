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
def generate_comedy_dialogue(words):
    try:
        prompt = (
            f"Create a short and funny conversation between a chubby, playful man named Tom and a cute girl named Lisa. "
            f"The conversation must naturally include these three words: {', '.join(words)}. "
            f"Make it friendly and humorous, about 5-8 lines. "
            f"First output the English conversation, then provide a fluent Japanese translation right below it, clearly separated."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative writer specializing in funny dialogues."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"会話生成エラー: {e}")
        return "会話の生成に失敗しました。"

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

# モード選択
mode = st.sidebar.selectbox("Select Mode", ["Word Registration", "Comedy Dialogue Creation", "Word List"])

# Word Registrationモード
if mode == "Word Registration":
    st.header("Word Registration Mode")
    word_input = st.text_input("Enter an English word")
    if st.button("Register Word"):
        if word_input.strip():
            words = load_words()
            words.append(word_input.strip())
            save_words(words)
            st.success(f"'{word_input}' を登録しました！")

# Comedy Dialogue Creationモード
elif mode == "Comedy Dialogue Creation":
    st.header("Comedy Dialogue Creation Mode")
    words = load_words()

    if len(words) < 3:
        st.warning("単語を3つ以上登録してください。")
    else:
        if "selected_words" not in st.session_state:
            st.session_state.selected_words = []

        if st.button("Select 3 Words"):
            st.session_state.selected_words = random.sample(words, 3)

        if st.session_state.selected_words:
            st.subheader("Selected Words")
            st.write(", ".join(st.session_state.selected_words))

            if st.button("Generate Comedy Dialogue"):
                dialogue = generate_comedy_dialogue(st.session_state.selected_words)
                st.subheader("Generated Dialogue")
                st.write(dialogue)

# Word Listモード
elif mode == "Word List":
    st.header("Word List Mode")
    words = load_words()

    if not words:
        st.info("まだ単語が登録されていません。")
    else:
        st.subheader("現在登録されている単語")

        for idx, word in enumerate(words):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- {word}")
            with col2:
                if st.button("Delete", key=f"delete_{idx}"):
                    words.pop(idx)
                    save_words(words)
                    st.rerun()

    st.subheader("新しい単語を追加")
    new_word = st.text_input("New Word", key="new_word")
    if st.button("Add Word"):
        if new_word.strip():
            words.append(new_word.strip())
            save_words(words)
            st.success(f"'{new_word}' を追加しました！")
            st.rerun()
