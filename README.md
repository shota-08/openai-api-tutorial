# 補足
- systemファイルの設定は以下

```
[Unit]
Description=Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/openai-api-tutorial
ExecStart=/home/ubuntu/openai-api-tutorial/.venv/bin/streamlit run home.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```