import streamlit as st
from openai import OpenAI
import base64
import uuid
import json
import os

from secrets_manager import get_secret
from cloudwatch_logger import setup_cloudwatch_logs, send_to_cloudwatch_logs

# openai
client = OpenAI()

# cloud watch log
log_stream = "02_picture"

# prompt path
PROMPT_FILE = "./prompts/01_サンプル.md"
USER_NAME = "user"
ASSISTANT_NAME = "assistant"


def init_page():
    st.set_page_config(
        page_title="my gpt",
        page_icon="📚"
    )
    st.title("gpt-4o chat")
    if "chat_log_02" not in st.session_state:
        st.session_state.chat_log_02 = []
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
    """ システムプロンプトの取得 """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def png_upload():
    """ PNGファイルのアップローダー """
    uploaded_file = st.file_uploader(
        label = "画像をドロップしてください",
        type = ["jpg", "jpeg", "png"],
        accept_multiple_files=False
    )
    # アップロードされたPNGファイルをtemp_pathに上書き保存
    if uploaded_file:
        return uploaded_file.read()
    else:
        return None


def encode_image(image_data):
    """ 画像をBase64エンコード """
    return base64.b64encode(image_data).decode("utf-8")


def get_llm_response(query, base64_image):
    """ LLMにクエリを送信し、回答を取得 """
    prompt = get_prompt(PROMPT_FILE)
    recent_log = st.session_state.chat_log_02
    messages = [
        {"role":"system", "content": prompt}
    ]
    for entry in recent_log:
        if entry["name"] == "user":
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": entry["msg"]},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{entry['image']}"}}
                ]
            })
        else:
            messages.append({"role": "assistant", "content": entry["msg"]})
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": query},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    })
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )
    answer = response.choices[0].message.content
    return answer


def show_png(image_data):
    """ 写真表示 """
    st.image(image_data)


def handle_log(query, answer, base64_image):
    """ ログの処理 """
    # CloudWatchにログを送信
    session_id = st.session_state["session_id"]
    user_log = {"id": session_id, "role": USER_NAME, "prompt_path": PROMPT_FILE, "content": query, "image_url": base64_image}
    assistant_log = {"id": session_id, "role": ASSISTANT_NAME, "prompt_path": PROMPT_FILE, "content": answer, "image_url": base64_image}
    send_to_cloudwatch_logs(log_stream, json.dumps(user_log, ensure_ascii=False))
    send_to_cloudwatch_logs(log_stream, json.dumps(assistant_log, ensure_ascii=False))

    # セッションにログを追加
    st.session_state.chat_log_02.append({"name": USER_NAME, "msg": query})
    st.session_state.chat_log_02.append({"name": ASSISTANT_NAME, "msg": answer})


def chat_interface(base64_image):
    """ チャット機能 """
    # ログ表示
    for chat in st.session_state.chat_log_02:
        with st.chat_message(chat["name"]):
            st.write(chat["msg"])

    query = st.chat_input('回答を入力')
    if query:
        try:
            answer = get_llm_response(query, base64_image)

            with st.chat_message("user"):
                st.write(query)

            with st.chat_message("assistant"):
                st.write(answer)

            # ログの追加
            handle_log(query, answer, base64_image)

        except Exception as e:
            st.error(f"error: {e}", icon="🚨")


def main():
    initialize_api_key()
    setup_cloudwatch_logs(log_stream)
    init_page()
    image_data = png_upload()
    if image_data:
        base64_image = encode_image(image_data)
        show_png(image_data)
        chat_interface(base64_image)


if __name__ == '__main__':
    main()