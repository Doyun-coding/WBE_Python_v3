import redis
import time
import threading

# Redis 클라이언트 설정 (DB 2 사용)
r = redis.Redis(host='localhost', port=6379, db=2)


# Redis 설정 확인 및 notify-keyspace-events 설정
def ensure_notify_keyspace_events():
    current_config = r.config_get("notify-keyspace-events").get("notify-keyspace-events", "")
    if "E" not in current_config or "x" not in current_config:
        print(f"[설정 변경] 현재 설정: '{current_config}', notify-keyspace-events 설정 중...")
        r.config_set("notify-keyspace-events", "Ex")
    else:
        print(f"[설정 확인] notify-keyspace-events는 이미 '{current_config}'로 설정됨")


# 리스너 실행 함수 (별도 스레드로 실행)
def listen_to_expire_events():
    p = r.pubsub()
    p.psubscribe('__keyevent@2__:expired')
    print("[리스너] 키 만료 이벤트 대기 중...")
    for message in p.listen():
        if message['type'] == 'pmessage':
            print(f"[리스너] 만료 이벤트 수신: {message['data'].decode()}")


# 키 설정 및 테스트 함수
def test_key_expiry():
    print("[테스트] testkey123 키를 설정합니다. (5초 후 만료)")
    r.set('testkey123', 'hello', ex=5)


# 메인 실행
if __name__ == "__main__":
    ensure_notify_keyspace_events()

    # 리스너를 백그라운드 스레드에서 실행
    listener_thread = threading.Thread(target=listen_to_expire_events, daemon=True)
    listener_thread.start()

    # 테스트 키 설정
    time.sleep(1)
    test_key_expiry()

    # 메인 스레드는 대기 (리스너가 동작할 수 있도록)
    while True:
        time.sleep(1)
