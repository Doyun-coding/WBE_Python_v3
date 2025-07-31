import asyncio
import logging

from config.redis_config import redis_client
from spell.spell_message_generator import generate_spell_cool_down_message
from worker.tts.tts_worker_process import generate_tts_mp3


# Redis Expire 이벤트 수신 하는 리스너 함수
def listen_for_expired_key():
    pubsub = redis_client.pubsub()
    pubsub.psubscribe('__keyevent@2__:expired')  # Redis DB 2의 만료 이벤트 구독

    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            expired_key = message['data']
            logging.info(f"키 만료 감지: {expired_key}")

            try:
                parts = expired_key.split(":")
                summoner_id = parts[1]
                champion_name = parts[2]
                spell_name = parts[3]

                from ws.ws_audio_server import user_sessions

                if summoner_id in user_sessions:
                    session = user_sessions[summoner_id]
                    audio_queue = session['audio_queue']
                    loop = session['loop']

                    # 쿨다운 완료 메세지 생성
                    spell_cool_down_message = generate_spell_cool_down_message(champion_name, spell_name)
                    logging.info(f"쿨다운 완료 메세지: {summoner_id} : {spell_cool_down_message}")

                    # 쿨다운 완료 메세지 음성으로 생성
                    tts_cd = generate_tts_mp3(spell_cool_down_message)
                    if tts_cd:
                        # WebSocket 송신 큐에 mp3 데이터 비동기 전송
                        asyncio.run_coroutine_threadsafe(audio_queue.put(tts_cd), loop)
                else:
                    logging.info(f"summoner_id '{summoner_id}'에 대한 오디오 컨텍스트 없음")

            except IndexError:
                print(f"잘못된 키 형식: {expired_key}")
