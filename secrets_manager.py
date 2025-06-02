import boto3
import streamlit as st
import json

def get_secret(secret_name, region_name):
    """ AWS Secrets Managerからシークレットを取得 """
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        st.error(f"シークレット '{secret_name}' の取得中にエラーが発生: {e}")
        st.stop()
        return None

    # シークレットの値が文字列またはバイナリとして返される
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        secret = get_secret_value_response['SecretBinary'].decode('utf-8')

    # シークレットがJSON形式の場合、パースする
    try:
        # Secrets Managerにキー/値のペアで保存した場合
        secret_dict = json.loads(secret)
        return secret_dict
    except json.JSONDecodeError:
        # JSON形式でない場合
        return secret