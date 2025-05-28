import streamlit as st
from openai import OpenAI
import uuid
import json

from dotenv import load_dotenv
load_dotenv()

# openai
client = OpenAI()

# prompt path
PROMPT_FILE = "./prompts/01_サンプル.md"

# 定数定義
USER_NAME = "user"
ASSISTANT_NAME = "assistant"


def init_page():
    st.set_page_config(
        page_title="my gpt",
        page_icon="📚"
    )
    st.title("gpt-4o chat")
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []


def get_prompt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_llm_response(query, recent_log):
    prompt = get_prompt(PROMPT_FILE)
    conversation_log = [
        {"role": "system", "content": prompt}
    ]
    conversation_log += [
        {"role": "assistant", "content": entry["msg"]} if entry["name"] == ASSISTANT_NAME else {"role": "user", "content": entry["msg"]}
        for entry in recent_log
    ]
    conversation_log.append({"role": "user", "content": query})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_log,
        temperature=0
    )
    answer = response.choices[0].message.content
    return answer


def chat_interface():
    # ログ表示
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.write(chat["msg"])

    query = st.chat_input('回答を入力')
    if query:
        try:
            recent_log = st.session_state.chat_log
            answer = get_llm_response(query, recent_log)

            with st.chat_message(USER_NAME):
                st.write(query)

            with st.chat_message(ASSISTANT_NAME):
                st.write(answer)

            # セッションにログを追加
            st.session_state.chat_log.append({"name" : USER_NAME, "msg" : query})
            st.session_state.chat_log.append({"name" : ASSISTANT_NAME, "msg" : answer})

        except Exception as e:
            st.error(f"error: {e}", icon="🚨")

    if not query and st.session_state.chat_log == []:
        first_chat = "自由に話してね。"
        with st.chat_message(ASSISTANT_NAME):
            st.write(first_chat)
        st.session_state.chat_log.append({"name" : ASSISTANT_NAME, "msg" : first_chat})


def main():
    init_page()
    chat_interface()


if __name__ == '__main__':
    main()
