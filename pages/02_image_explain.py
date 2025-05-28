import streamlit as st
from openai import OpenAI
import base64
import os

from dotenv import load_dotenv
load_dotenv()

# openai
client = OpenAI()

PROMPT_FILE = "./prompts/01_サンプル.md"
UPLOAD_FOLDER = "./temp_upload"
UPLOAD_FILENAME = "uploaded_image"


def init_page():
    st.set_page_config(
        page_title="my gpt",
        page_icon="📚"
    )
    st.title("gpt-4o chat")
    if "chat_log_02" not in st.session_state:
        st.session_state.chat_log_02 = []


def get_prompt(filepath):
    """ システムプロンプトの取得 """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def prepare_directory(path):
    """ ディレクトリが存在しない場合に作成 """
    os.makedirs(path, exist_ok=True)


def png_upload():
    """ PNGファイルのアップローダー """
    uploaded_file = st.file_uploader(
        label = "画像をドロップしてください",
        type = ["jpg", "jpeg", "png"],
        accept_multiple_files=False
    )
    prepare_directory(UPLOAD_FOLDER)

    # アップロードされたPNGファイルをtemp_pathに上書き保存
    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        temp_path = os.path.join(UPLOAD_FOLDER, f"{UPLOAD_FILENAME}.{file_extension}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        return temp_path
    else:
        return None


def encode_image(temp_path):
    """ 画像をBase64エンコード """
    with open(temp_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_llm_response(query, temp_path):
    """ LLMにクエリを送信し、回答を取得 """
    prompt = get_prompt(PROMPT_FILE)
    recent_log = st.session_state.chat_log_02
    base64_image = encode_image(temp_path)
    messages = [
        {"role":"system", "content": prompt}
    ]
    for entry in recent_log:
        if entry["name"] == "user":
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": entry["msg"]},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{entry['image']}" }}
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
    # ユーザー入力と生成された回答をログに追加
    st.session_state.chat_log_02.append({"name" : "user", "msg" : query, "image": base64_image})
    st.session_state.chat_log_02.append({"name" : "assistant", "msg" : answer})
    return answer


def show_png(temp_path):
    """ 写真表示 """
    st.image(temp_path)


def chat_interface(temp_path):
    """ チャット機能 """
    # ログ表示
    for chat in st.session_state.chat_log_02:
        with st.chat_message(chat["name"]):
            st.write(chat["msg"])

    query = st.chat_input('回答を入力')
    if query:
        answer = get_llm_response(query, temp_path)

        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            st.write(answer)


def main():
    init_page()
    temp_path = png_upload()
    if temp_path:
        show_png(temp_path)
        chat_interface(temp_path)


if __name__ == '__main__':
    main()