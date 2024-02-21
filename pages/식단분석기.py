import streamlit as st
from openai import OpenAI
import boto3
from botocore.exceptions import NoCredentialsError
import os

# AWS S3 설정
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
BUCKET_NAME = st.secrets["BUCKET_NAME"]

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_to_s3(file, bucket_name, object_name=None):
    if object_name is None:
        object_name = file.name
    try:
        response = s3.upload_fileobj(file, bucket_name, object_name)
        return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    except NoCredentialsError:
        print("Credentials not available")
        return None

# OpenAI 클라이언트 객체 생성
client = OpenAI(api_key=st.secrets["api_key"])

st.set_page_config(layout="wide")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요:", type="password")
correct_password = st.secrets["password"]

if password == correct_password:
    st.title("식단분석기")

    uploaded_file = st.file_uploader("방금 먹은 식사를 업로드하세요.", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_url = upload_to_s3(uploaded_file, BUCKET_NAME)
        if file_url:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "음식을 분석해주고 모자란 영양소를 알려주세요."},
                            {"type": "image_url", "image_url": {"url": file_url}},
                        ],
                    }
                ],
                max_tokens=300,
            )
            # 필요한 부분만 추출하여 출력
            if response.choices and response.choices[0].finish_reason == 'stop':
                description = response.choices[0].message.content  # 수정된 부분
                st.write(description)
            else:
                st.write("이미지 분석 결과를 가져오는 데 실패했습니다.")
else:
    st.warning("올바른 비밀번호를 입력해주세요.")
