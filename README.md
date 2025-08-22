# 🎮 LOLPAGO - 리그 오브 레전드 실시간 음성 채팅 분석 시스템

## 📋 개요

LOLPAGO는 리그 오브 레전드 게임 중 실시간 음성 채팅을 분석하여 챔피언의 스펠(소환사 주문) 사용 정보를 자동으로 추적하고 관리하는 AI 기반 시스템입니다.

### 🎯 주요 기능
- **실시간 음성 인식**: WebSocket을 통한 실시간 음성 스트리밍 처리
- **AI 음성 분석**: OpenAI Whisper를 활용한 고정밀 음성-텍스트 변환
- **스마트 텍스트 정제**: GPT-4를 통한 게임 컨텍스트 기반 텍스트 분석
- **스펠 쿨다운 관리**: Redis를 활용한 실시간 스펠 쿨다운 추적
- **음성 피드백**: TTS를 통한 스펠 상태 음성 알림

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   클라이언트    │ ◄─────────────► │  WebSocket 서버 │
│  (게임 클라이언트) │                │   (ws:8888)     │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
┌─────────────────┐                ┌─────────────────┐
│   Redis DB      │ ◄─────────────► │  STT Worker     │
│ (스펠 쿨다운)   │                │ (Whisper + GPT) │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
                                   ┌─────────────────┐
                                   │  TTS Worker     │
                                   │ (음성 생성)     │
                                   └─────────────────┘
```

## 🚀 기술 스택

### Backend
- **Python 3.8+**: 메인 개발 언어
- **asyncio**: 비동기 처리
- **WebSocket**: 실시간 양방향 통신
- **Redis**: 스펠 쿨다운 데이터 저장 및 이벤트 처리

### AI/ML
- **OpenAI Whisper**: 음성 인식 (large 모델)
- **OpenAI GPT-4**: 텍스트 정제 및 분석
- **OpenAI TTS**: 텍스트-음성 변환
- **WebRTC VAD**: 음성 활동 감지

### 오디오 처리
- **NumPy**: 수치 연산
- **SciPy**: 오디오 파일 처리
- **SoundDevice**: 오디오 스트리밍

## 📁 프로젝트 구조

```
WBE_Python/
├── config/                     # 설정 파일
│   ├── __init__.py
│   ├── log_config.py          # 로깅 설정
│   └── redis_config.py        # Redis 연결 설정
├── prompt/                     # AI 프롬프트
│   └── champion_spell_prompt.txt  # 챔피언/스펠 분석 프롬프트
├── spell/                      # 스펠 관련 로직
│   ├── spell_service.py       # 스펠 쿨다운 관리 서비스
│   └── spell_message_generator.py  # 스펠 메시지 생성
├── worker/                     # 워커 프로세스
│   ├── stt/                   # 음성 인식 워커
│   │   ├── stt_worker_process.py  # Whisper + GPT 파이프라인
│   │   └── util/
│   │       └── stt_worker_util.py # 음성 활동 감지
│   ├── tts/                   # 음성 합성 워커
│   │   └── tts_worker_process.py  # TTS 생성
│   └── redis/                 # Redis 이벤트 처리
│       └── redis_expire_listener.py  # 키 만료 리스너
├── ws/                        # WebSocket 서버
│   └── ws_audio_server.py     # 메인 WebSocket 서버
├── main.py                    # 애플리케이션 진입점
├── requirements.txt           # Python 의존성
└── README.md                  # 프로젝트 문서
```

## 🛠️ 설치 및 실행

### 1. 환경 요구사항
- Python 3.8 이상
- Redis 서버
- OpenAI API 키

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
WHISPER_MODEL=large

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. 서버 실행
```bash
python main.py
```

서버가 `ws://0.0.0.0:8888`에서 실행됩니다.

## 🔧 주요 기능 상세

### 1. 실시간 음성 처리
- **WebSocket 연결**: 클라이언트와 실시간 양방향 통신
- **음성 활동 감지**: WebRTC VAD를 통한 음성 구간 자동 감지
- **오디오 스트리밍**: 실시간 오디오 데이터 처리

### 2. AI 음성 분석
- **Whisper 모델**: OpenAI의 large 모델을 사용한 고정밀 음성 인식
- **GPT-4 정제**: 게임 컨텍스트에 맞는 텍스트 정제 및 분석
- **챔피언/스펠 매핑**: 줄임말 및 별칭을 정확한 이름으로 변환

### 3. 스펠 쿨다운 관리
- **Redis 저장**: 스펠 사용 시 쿨다운 정보를 Redis에 저장
- **실시간 추적**: 키 만료 이벤트를 통한 쿨다운 완료 감지
- **스킬 가속 계산**: 게임 내 스킬 가속 수치 반영

### 4. 음성 피드백
- **TTS 생성**: OpenAI TTS를 통한 자연스러운 음성 생성
- **실시간 전송**: WebSocket을 통한 즉시 음성 피드백

## 🎮 사용법

### 클라이언트 연결
```javascript
const ws = new WebSocket('ws://localhost:8888');

// 초기화 메시지 전송
ws.send(JSON.stringify({
    type: "init",
    summonerId: "your_summoner_id",
    region: "KR"
}));

// 음성 데이터 전송
ws.send(audioData); // 바이너리 오디오 데이터

// TTS 응답 수신
ws.onmessage = function(event) {
    if (event.data instanceof Blob) {
        // MP3 음성 데이터 처리
        playAudio(event.data);
    }
};
```

### 지원하는 챔피언 및 스펠
- **챔피언**: 150+ 챔피언 지원 (줄임말 포함)
- **스펠**: 점멸, 순간이동, 점화, 회복, 탈진, 정화, 방어막, 유체화, 강타

## 🔍 API 엔드포인트

### 스펠 정보 전송
```
POST https://lolpago.com/api/spell
Content-Type: application/json

{
    "summonerId": "string",
    "finalText": "string",
    "region": "string"
}
```

## 📊 성능 최적화

- **멀티스레딩**: ThreadPoolExecutor를 통한 병렬 처리
- **비동기 처리**: asyncio를 활용한 효율적인 I/O 처리
- **메모리 관리**: 임시 파일 자동 정리
- **연결 풀링**: Redis 연결 최적화

## 🐛 문제 해결

### 일반적인 문제들

1. **Whisper 모델 로딩 실패**
   - 인터넷 연결 확인
   - OpenAI API 키 유효성 검증

2. **Redis 연결 오류**
   - Redis 서버 실행 상태 확인
   - 환경 변수 설정 검증

3. **오디오 처리 오류**
   - 오디오 포맷 확인 (16kHz, 16bit)
   - 마이크 권한 확인

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 생성해 주세요.

---

**LOLPAGO** - 리그 오브 레전드 게임을 더욱 스마트하게! 🎮✨
