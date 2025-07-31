from bark import SAMPLE_RATE, generate_audio
from bark.generation import preload_models
import scipy

preload_models()
text_prompt = "안녕하세요. 당신을 만나서 정말 반가워요."
audio_array = generate_audio(text_prompt)

scipy.io.wavfile.write("bark_output.wav", SAMPLE_RATE, audio_array)