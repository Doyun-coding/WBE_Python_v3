import asyncio
import os
import requests
import tempfile
import logging
import time

import numpy as np
import whisper
from dotenv import load_dotenv
from openai import OpenAI

from spell.spell_message_generator import generate_spell_check_message
from spell.spell_service import save_spell_cool_down
from worker.tts.tts_worker_process import generate_tts_mp3

# 환경 변수 로딩
load_dotenv()

# OpenAI API 키 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")
# OpenAI 클라이언트 객체 생성
client = OpenAI(api_key=openai_api_key)
# Whisper 모델 로딩 (large 모델 사용)
model = whisper.load_model("large")


# OpenAI 프롬프트 템플릿 파일 불러오는 메서드
def load_prompt_template(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# 음성 -> 텍스트 -> GPT 분석 -> TTS 응답 -> WebSocket 전송까지 담당하는 파이프라인
def whisper_pipeline(summoner_id, region, audio_data, audio_queue, loop):
    logging.info(f"[🔊 Whisper] {summoner_id} 음성 분석 시작")

    start_time = time.time()  # 시작 시간 기록

    # 입력된 float32 PCM 오디오 데이터 임시 wav 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        from scipy.io import wavfile
        wavfile.write(tmpfile.name, 16000, (audio_data * 32768).astype(np.int16))
        path = tmpfile.name

    # Whisper 모델로 음성 인식 (음성을 텍스트 변환)
    result = model.transcribe(path)
    raw_text = result["text"]
    os.remove(path)  # 임시 파일 삭제

    # stt 결과 출력
    logging.info(f"[raw_text] : {raw_text}")

    # GPT 에 전달할 프롬프트 로드 및 텍스트 삽입
    prompt_template = load_prompt_template("prompt/champion_spell_prompt.txt")
    prompt = prompt_template.format(raw_text=raw_text)

    # 프롬프트 이용 하여 GPT-4 모델 호출
    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
    except Exception as e:
        logging.info(f"[GPT 호출 오류]: {e}")
        return

    # GPT 응답에서 정제된 최종 텍스트 추출
    final_text = gpt_response.choices[0].message.content.strip()
    logging.info(f"[🎯 결과] {summoner_id}: {final_text}")

    # Spring 서버로 결과 전송 ([챔피언 이름] [스펠 이름])
    # response = requests.post("http://localhost:8080/spell", json={
    response = requests.post("https://lolpago.com/api/spell", json={
        "summonerId": summoner_id,
        "finalText": final_text,
        "region": region
    })

    elapsed_time = time.time() - start_time  # 측정 종료

    # Spring 서버 응답 CREATED 아니면 에러 처리
    if response.status_code != 201:
        logging.info(f"Spring 서버 응답 실패: {response.status_code} - {response.text}")
        return

    # 서버 응답 데이터 파싱
    response_data = response.json()

    # 응답 데이터 타입이 spell 인 경우
    if response_data["type"] == 'spell':
        champion_name = response_data["championName"]
        spell_name = response_data["spellName"]

        # redis 스펠 쿨다운 정보 저장
        save_spell_cool_down(
            response_data["summonerId"], response_data["championName"], response_data["spellName"],
            response_data["spellCoolTime"], response_data["skillAbilityHaste"], int(elapsed_time)
        )

        # 🎧 TTS 생성 (mp3 binary 반환)
        spell_check_message = generate_spell_check_message(champion_name, spell_name)
        tts_cd = generate_tts_mp3(spell_check_message)
        if tts_cd:
            # WebSocket 송신 큐에 TTS mp3 데이터 넣기 (비동기 처리)
            asyncio.run_coroutine_threadsafe(audio_queue.put(tts_cd), loop)
