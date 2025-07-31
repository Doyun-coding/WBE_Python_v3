# 스펠 체크 응답 메세지 생성
def generate_spell_check_message(champion_name: str, spell_name: str) -> str:
    return f"{champion_name} {spell_name} 쿨타임 등록했습니다!"


# 스펠 쿨다운 완료 메세지 생성
def generate_spell_cool_down_message(champion_name: str, spell_name: str) -> str:
    return f"{champion_name} {spell_name} 돌았습니다!"
