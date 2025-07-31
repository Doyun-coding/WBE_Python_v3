import asyncio
import threading
import logging

import websockets
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor
from worker.stt.util.stt_worker_util import VoiceActivityDetector
from worker.stt.stt_worker_process import whisper_pipeline
from worker.redis.redis_expire_listener import listen_for_expired_key

# 최대 11개의 쓰레드를 가지는 쓰레들 풀 생성
executor = ThreadPoolExecutor(max_workers=11)

# summoner_id를 키로 하는 오디오 큐와 이벤트 루프를 저장하는 딕셔너리
user_sessions = {}
# Redis Expire 이벤트 리스너 시작 플래그
redis_listener_started = False


async def handle_connection(websocket):
    logging.info("🎧 클라이언트 연결됨")

    # 소환사의 summoner_id 값을 가져오는 코드
    while True:
        init_message = await websocket.recv()
        if isinstance(init_message, str):
            try:
                data = json.loads(init_message)
                if data.get("type") == "init":
                    summoner_id = data.get("summonerId", "unknown")
                    region = data.get("region", "KR")
                    logging.info(f"🎮 Summoner ID: {data.get('summonerId', 'unknown')} 🌍 Region: {data.get('region', 'KR')}")
                    break
            except json.JSONDecodeError:
                logging.info("❌ 초기화 메시지 파싱 오류")
        else:
            logging.info("❌ 초기화 메시지가 JSON 형식이 아님")

    # stt_worker_util.py 에서 음성 활동 감지 및 녹음 처리를 위한 VoiceActivityDetector 객체 생성
    vad = VoiceActivityDetector()
    # Summoner ID와 오디오 큐 초기화
    audio_queue = asyncio.Queue()
    # 비동기 이벤트 루프 가져오기
    loop = asyncio.get_event_loop()

    # user_sessions 에 summoner_id를 키로 하는 오디오 큐, 이벤트 루프, WebSocket 저장
    user_sessions[summoner_id] = {
        "audio_queue": audio_queue,
        "loop": loop,
        "websocket": websocket
    }

    # TTS 결과를 WebSocket 으로 클라이언트에게 전송하는 비동기 함수
    async def tts_sender():
        while True:
            # audio_queue 에서 오디오 데이터를 가져온다
            mp3_data = await audio_queue.get()
            try:
                # WebSocket 을 통해 음성 데이터를 클라이언트로 전송한다
                await websocket.send(mp3_data)
                logging.info("📤 mp3 전송 완료")
            except Exception as e:
                logging.info(f"❌ WebSocket 전송 에러: {e}")
            finally:
                # 작업이 완료되었음을 audio_queue에 알린다
                audio_queue.task_done()

    # TTS 전송 작업을 비동기적으로 시작
    tts_task = asyncio.create_task(tts_sender())

    try:
        # WebSocket 메시지를 비동기적으로 수신
        async for message in websocket:
            # 메시지가 "ping" 문자열인 경우 무시
            if isinstance(message, str) and message == "ping":
                continue
            # 메시지가 바이트가 아닌 경우 무시
            if not isinstance(message, bytes):
                continue

            # 음성 활동 감지 및 녹음 처리
            pcm = np.frombuffer(message, dtype=np.int16).astype(np.float32) / 32768.0
            result = vad.process_audio(pcm)

            # 음성 활동이 감지되면 녹음된 오디오 데이터를 Whisper 파이프라인으로 전달
            if result is not None:
                logging.info("🛑 음성 녹음 종료 → Whisper 분석 시작")
                loop.run_in_executor(executor, whisper_pipeline, summoner_id, region, result, audio_queue, loop)

    # WebSocket 연결이 종료되거나 예외가 발생
    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"예외 발생 WebSocket 연결 종료됨: {e}")
    finally:
        # TTS 전송 작업을 종료
        tts_task.cancel()

        # 연결 종료 시 summoner_id 제거
        if summoner_id in user_sessions:
            del user_sessions[summoner_id]

        logging.info("WebSocket 정상적 연결 종료")


# WebSocket 서버를 시작하는 비동기 함수
async def start_websocket_server():
    global redis_listener_started

    logging.info("📡 WebSocket 서버 시작 (ws://0.0.0.0:8888)")

    if not redis_listener_started:
        redis_thread = threading.Thread(target=listen_for_expired_key, daemon=True)
        redis_thread.start()
        redis_listener_started = True

    # 클라이언트가 WebSocket 연결을 시도할 때마다 handle_connection 함수가 코루틴을 새로 실행해준다
    async with websockets.serve(handle_connection, "0.0.0.0", 8888, max_size=2**22, ping_interval=None,):
        # 서버가 종료되지 않도록 무한 대기
        await asyncio.Future()
