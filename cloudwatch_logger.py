import boto3
import streamlit as st
from datetime import datetime, timezone

region_name = "ap-northeast-1" # AWSリージョン
logs_client = boto3.client('logs', region_name=region_name)
log_group = "streamlit-llm-tutorial"


def setup_cloudwatch_logs(log_stream):
    """ CloudWatch Logsクライアントを初期化 """
    # ロググループの作成
    try:
        logs_client.create_log_group(logGroupName=log_group)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass

    # ログストリームの作成
    try:
        logs_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass


def send_to_cloudwatch_logs(log_stream, message):
    """ CloudWatch Logsにログイベントを送信 """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    try:
        logs_client.put_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            logEvents=[{'timestamp': timestamp, 'message': message}]
        )
    except Exception as e:
        st.error(f"ログ処理中にエラーが発生: {e}")
        st.stop()
        return None