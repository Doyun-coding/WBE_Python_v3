import logging

from config.redis_config import redis_client
from spell.spell_message_generator import generate_spell_cool_down_message


# 스펠 쿨다운 정보를 Redis 저장하는 함수
def save_spell_cool_down(
        summoner_id: int, champion_name: str, spell_name: str,
        spell_cool_time: int, skill_ability_haste: int, elapsed_time: int = 0):
    spell_cool_down_redis_key = f"spell:{summoner_id}:{champion_name}:{spell_name}"
    spell_cool_down_redis_value = generate_spell_cool_down_message(champion_name, spell_name)

    expire_cool_time = calculate_spell_cool_time(spell_cool_time, skill_ability_haste)
    expire_cool_time -= elapsed_time    # 경과 시간 제외

    # Redis 스펠 쿨다운 정보 저장
    logging.info(f"[Redis 저장] {spell_cool_down_redis_key} : {spell_cool_down_redis_value} (쿨타임: {expire_cool_time}s)")
    redis_client.set(spell_cool_down_redis_key, spell_cool_down_redis_value, ex=expire_cool_time)


# 스킬 가속을 통한 스펠 쿨타운 계산
def calculate_spell_cool_time(spell_cool_time: int, skill_ability_haste: int) -> int:
    # 스킬 가속 적용
    expire_cool_time = spell_cool_time / (1 + (skill_ability_haste / 100))

    return int(expire_cool_time)
