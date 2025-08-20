import logging
import webrtcvad
import collections
import numpy as np


# 실시간 음성 감지 및 녹음을 위한 클래스
class VoiceActivityDetector:
    # VoiceActivityDetector 생성자 초기화
    def __init__(self, sample_rate=16000, frame_duration_ms=30, silence_threshold=33, volume_threshold=0.7):
        # 오디오 샘플링 주파수 (Hz) - 일반적으로 16kHz 사용
        self.sample_rate = sample_rate
        # 1 프레임 길이 (ms 단위) - 30ms가 일반적
        self.frame_duration_ms = frame_duration_ms
        # 프레임 당 샘플 수 = 샘플링 주파수 X 프레임 지속시간 / 1000
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        # 무음이 감지될 수 있는 최대 프레임 수 (30ms x 33 = 약 1초)
        self.silence_threshold = silence_threshold
        # 음성 최소 볼륨 감지 임계값 (0.7 이상이면 음성으로 간주)
        self.volume_threshold = volume_threshold

        # 음성 감지 객체 생성 (3은 민감도 설정)
        self.vad = webrtcvad.Vad(3)
        # reset 메서드 호출 (내부 상태 초기화)
        self.reset()

    # 내부 상태 초기화 메서드
    def reset(self):
        # 현재 음성 녹음 중인지 여부
        self.triggered = False
        # 무음이 감지된 프레임 수
        self.silence_count = 0
        # 최근 무음 프레임을 버퍼에 저장
        self.ring_buffer = collections.deque(maxlen=self.silence_threshold)
        # 전체 녹음된 오디오 프레임 리스트
        self.recording = []

    # WebRTC VAD로 음성 여부 판단
    def is_speech(self, pcm):
        # float PCM -> init16 PCM -> 바이트로 변환
        pcm_bytes = (pcm * 32768).astype(np.int16).tobytes()
        # WebRTC VAD에 바이트 오디오 전달하여 음성 여부 반환
        return self.vad.is_speech(pcm_bytes, self.sample_rate)

    # PCM 데이터를 받아 음성 여부 판단 및 녹음 처리
    def process_audio(self, pcm):
        """
        실시간으로 PCM 데이터를 받아 음성을 감지하고,
        무음 1초 지속 시 녹음을 종료하고 최종 오디오 데이터를 반환한다.

        :param pcm: float32 PCM (normalized -1.0 ~ 1.0)
        :return: 녹음 종료 시 np.ndarray 반환, 계속 녹음 중이면 None
        """
        samples_per_frame = self.frame_size
        # 총 프레임 수 계산
        num_frames = len(pcm) // samples_per_frame

        # 입력된 PCM 프레임을 구성할 만큼 충분하지 않으면 처리하지 않는다
        if num_frames == 0:
            return None

        # PCM 데이터를 프레임 단위로 처리
        for i in range(num_frames):
            frame = pcm[i * samples_per_frame:(i + 1) * samples_per_frame]

            # 볼륨 계산 (절댓값 중 최대값)
            volume = np.max(np.abs(frame))
            if volume < self.volume_threshold:
                speech = False
            else:
                # WebRTC VAD로 실제 음성 여부 판단
                speech = self.is_speech(frame)

            logging.debug(f"{'🎙️ 감지됨' if speech else '🔈 무음'} | volume={volume:.4f}")

            # 음성이 감지되면 녹음 상태로 전환
            if self.triggered:
                # 프레임 저장
                self.recording.append(frame)
                if not speech:
                    # 무음 카운트 증가
                    self.silence_count += 1
                    # 일정 시간 이상 무음이면 녹음 종료 (약 1초)
                    if self.silence_count > self.silence_threshold:
                        audio_data = np.concatenate(self.recording)
                        self.reset()
                        return audio_data
                else:
                    # 음성 감지 시 무음 카운터 초기화
                    self.silence_count = 0
            # 아직 녹음을 시작하지 않은 경우
            else:
                # 최근 프레임을 링버퍼에 저장
                self.ring_buffer.append(frame)
                if speech and volume > self.volume_threshold:
                    logging.info("🎤 음성 시작 → 녹음 시작")
                    # 녹음 시작
                    self.triggered = True
                    # 시작 전 무음도 포함
                    self.recording.extend(self.ring_buffer)
                    # 버퍼 초기화
                    self.ring_buffer.clear()

        return None # 녹음 종료 조건을 아직 충족하지 않으면 None 반환!
