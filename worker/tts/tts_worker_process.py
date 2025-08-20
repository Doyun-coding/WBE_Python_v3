import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로딩
load_dotenv()

# 환경 변수에서 OpenAI API 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
# OpenAI API 클라이언트 객체 생성
client = OpenAI(api_key=openai_api_key)


def generate_tts_mp3(spell_text: str) -> bytes:
    """
    입력된 텍스트(spell_text)를 OpenAI의 TTS(Text-to-Speech) 모델을 이용하여
    음성(mp3 바이너리)으로 변환하는 함수.

    Parameters:
        spell_text (str): 변환할 텍스트

    Returns:
        bytes: 변환된 음성 데이터 (mp3 형식의 바이너리)
               오류 발생 시 None 반환
    """
    try:
        # OpenAI TTS 모델을 이용하여 텍스트를 음성으로 변환
        tts = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=spell_text
        )
        # 생성된 mp3 오디오 바이너리 데이터를 반환
        return tts.content
    except Exception as e:
        logging.info(f"[TTS 생성 오류] {e}")
        # 에러 발생 시 None 반환
        return None
