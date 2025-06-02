import streamlit as st
from openai import OpenAI
import boto3
import uuid
import json
import os

from secrets_manager import get_secret
from cloudwatch_logger import setup_cloudwatch_logs, send_to_cloudwatch_logs

# openai
client = OpenAI()

# cloud watch log
log_stream = "01_chat"

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
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())


def initialize_api_key():
    """ AWS Secrets ManagerからAPIキーを取得し環境変数に設定する """
    secret_name = "openai-api-key" # シークレット名
    region_name = "ap-northeast-1" # AWSリージョン

    try:
        secret_value = get_secret(secret_name, region_name)
    except Exception as e:
        st.error(f"シークレット取得エラー: {e}")
        st.stop()
        return None

    openai_api_key = None
    if isinstance(secret_value, dict) and "OPENAI_API_KEY" in secret_value:
        openai_api_key = secret_value["OPENAI_API_KEY"]
    elif isinstance(secret_value, str):
        # シークレットが直接キーの値（JSONではない平文）として保存されている場合
        openai_api_key = secret_value

    if openai_api_key is None:
        st.error("OpenAI APIキーが見つかりません。Secrets Managerの設定を確認してください。")
        st.stop()

    os.environ["OPENAI_API_KEY"] = openai_api_key


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


def handle_log(query, answer):
    """ ログの処理 """
    # CloudWatchにログを送信
    session_id = st.session_state["session_id"]
    user_log = {"id": session_id, "role": USER_NAME, "prompt_path": PROMPT_FILE, "content": query}
    assistant_log = {"id": session_id, "role": ASSISTANT_NAME, "prompt_path": PROMPT_FILE, "content": answer}
    send_to_cloudwatch_logs(log_stream, json.dumps(user_log, ensure_ascii=False))
    send_to_cloudwatch_logs(log_stream, json.dumps(assistant_log, ensure_ascii=False))

    # セッションにログを追加
    st.session_state.chat_log.append({"name": USER_NAME, "msg": query})
    st.session_state.chat_log.append({"name": ASSISTANT_NAME, "msg": answer})


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

            # ログの追加
            handle_log(query, answer)

        except Exception as e:
            st.error(f"error: {e}", icon="🚨")

    if not query and st.session_state.chat_log == []:
        first_chat = "自由に話してね。"
        with st.chat_message(ASSISTANT_NAME):
            st.write(first_chat)
        st.session_state.chat_log.append({"name" : ASSISTANT_NAME, "msg" : first_chat})


def main():
    initialize_api_key()
    setup_cloudwatch_logs(log_stream)
    init_page()
    chat_interface()


if __name__ == '__main__':
    main()
