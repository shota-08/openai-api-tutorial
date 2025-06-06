import base64
from io import BytesIO
from PIL import Image
import streamlit as st

from config import OpenAIClient

# openai client
client = OpenAIClient()

def init_page():
    """ ページ設定 """
    st.set_page_config(
        page_title = "text2image x llm"
    )
    st.title("text2image x llm")
    if "chat_image_log" not in st.session_state:
        st.session_state.chat_image_log = []
    if "response_id" not in st.session_state:
        st.session_state.response_id = None


def get_llm_response(query):
    """ LLMにクエリを送信し、回答を取得 """
    if st.session_state.response_id is None or not st.session_state.chat_image_log:
        response = client.client.responses.create(
            model=client.image_model,
            input=query,
            tools=[{"type": "image_generation"}],
        )
    else:
        response = client.client.responses.create(
            model=client.image_model,
            previous_response_id=st.session_state.response_id,
            input=query,
            tools=[{"type": "image_generation"}],
        )
    st.session_state.response_id = response.id # ここで管理
    image_data = [
        output.result
        for output in response.output
        if output.type == "image_generation_call"
    ]
    if not image_data:
        st.error("申し訳ございません。画像を生成できませんでした。\n具体的に「○○を描いて」といった指示をいただけますと幸いです。")
        st.stop()
    image_base64 = image_data[0]
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_bytes)) # BytesIOを使って（保存されてない）メモリデータにopen関数を用いて画像化し、それをreturnします
    return image


def chat_interface():
    """ chat機能全般 """
    # ログ表示
    for message in st.session_state.chat_image_log:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                st.image(message["image"])
    query = st.chat_input("質問を入力")
    if query:
        answer = get_llm_response(query)
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            st.image(answer)

        # 履歴に追加
        st.session_state.chat_image_log.append({"role": "user", "content": query})
        st.session_state.chat_image_log.append({"role": "assistant", "image": answer})


def main():
    init_page()
    chat_interface()


if __name__ == "__main__":
    main()