import base64
from io import BytesIO
from PIL import Image
import streamlit as st

from config import OpenAIClient

# openai client
client = OpenAIClient()

# promptファイル
PROMPT_FILE = "./prompts/04_change.md"

def init_page():
    """ ページ設定 """
    st.set_page_config(
        page_title = "image2image x llm"
    )
    st.title("image2image x llm")
    if "image_image_log" not in st.session_state:
        st.session_state.image_image_log = []
    if "response_id" not in st.session_state:
        st.session_state.response_id = None


def get_prompt(filepath):
    """ システムプロンプトの取得 """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def png_upload():
    """ PNGファイルのアップローダー """
    picture = st.file_uploader(
        label="画像を選択",
        type=["png", "jpeg", "jpg"],
        accept_multiple_files=False
        )
    if picture:
        return picture.read()
    else:
        return None


def encode_image(pct_byte):
    """ 画像をBase64エンコード """
    return base64.b64encode(pct_byte).decode("utf-8")


def decode_image(pct_b64):
    """画像をBase64からバイト列にデコード"""
    return base64.b64decode(pct_b64)


def show_pct(pct_byte):
    """アップロードされた画像を表示"""
    st.image(pct_byte)


def get_llm_response(query, pct_b64=None):
    """ LLMにクエリを送信し、回答を取得 """
    if st.session_state.response_id is None or not st.session_state.image_image_log:
        # システムプロンプト
        prompt = get_prompt(PROMPT_FILE)
        messages = [{"role": "system", "content": prompt}]
        # 今回のプロンプト
        messages.append({
                "role": "user",
                "content": [
                    {"type": "input_text", "text": query},
                    {
                        "type": "input_image", "image_url": f"data:image/jpeg;base64,{pct_b64}"
                    }
                ]
            })
        response = client.client.responses.create(
            model=client.image_model,
            input=messages,
            tools=[{"type": "image_generation"}],
        )
    else:
        # 今回のプロンプト
        messages = [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": query}
                ]
            }]
        response = client.client.responses.create(
            model=client.image_model,
            previous_response_id=st.session_state.response_id,
            input=messages,
            tools=[{"type": "image_generation"}],
        )
    st.session_state.response_id = response.id # ここで管理
    image_data = [
        output.result
        for output in response.output
        if output.type == "image_generation_call"
    ]
    image_base64 = image_data[0]
    image_bytes = decode_image(image_base64)
    image = Image.open(BytesIO(image_bytes)) # BytesIOを使って（保存されてない）メモリデータにopen関数を用いて画像化し、それをreturnします
    return image


def chat_interface(pct_byte):
    """ chat機能全般 """
    # ログ表示
    for message in st.session_state.image_image_log:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
                st.image(decode_image(message["image"]))
            else:
                st.image(decode_image(message["image"]))
    pct_b64 = encode_image(pct_byte)
    query = st.chat_input("質問を入力")
    if query:
        answer = get_llm_response(query, pct_b64)
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            st.image(answer)
        # 戻り値の画像をバイトバッファに格納してbyteに変換後、base64変換
        buffer = BytesIO()
        answer.save(buffer, format="PNG")
        buffer.seek(0)
        answer_b64 = encode_image(buffer.read())
        # 履歴に追加
        st.session_state.image_image_log.append({"role": "user", "content": query, "image": pct_b64})
        st.session_state.image_image_log.append({"role": "assistant", "image": answer_b64})


def main():
    init_page()
    image = png_upload()
    if image:
        show_pct(image)
        chat_interface(image)


if __name__ == "__main__":
    main()