import streamlit as st

def init_page():
    st.set_page_config(
        page_title="個人用gpt4o",
        page_icon="📚"
    )
    st.info("☜ 選択してね")

def main():
    init_page()

if __name__ == '__main__':
    main()
