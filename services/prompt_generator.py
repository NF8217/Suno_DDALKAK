"""
AI를 이용한 Suno 프롬프트 생성기 (OpenAI or Anthropic)
"""
from typing import Optional
import config

# 장르별 레퍼런스 프롬프트
GENRE_REFERENCE = {
    "K-pop": "modern K-pop style, catchy chorus, clean production, strong rhythm, polished arrangement",
    "R&B": "smooth R&B groove, emotional vocal delivery, warm chords, slow to mid tempo, intimate atmosphere",
    "Ballad": "emotional ballad, piano-driven arrangement, slow tempo, heartfelt melody, expressive vocal",
    "EDM": "energetic EDM track, powerful drop, modern electronic sound, festival-style rhythm",
    "Lo-fi": "lo-fi chill beat, relaxed tempo, soft textures, nostalgic atmosphere, minimal arrangement",
    "Hip-hop": "modern hip-hop beat, strong rhythm, deep bass, atmospheric sound, confident delivery",
    "Rock": "modern rock style, electric guitar driven, dynamic energy, strong drums",
    "Jazz": "smooth jazz style, warm instruments, relaxed groove, late-night atmosphere",
    "시티팝": "retro city pop style, 80s inspired groove, nostalgic melody, smooth rhythm section",
    "클래식/OST": "cinematic orchestral style, emotional progression, dramatic atmosphere, cinematic score"
}


class PromptGenerator:
    """Suno용 음악 프롬프트 생성기"""

    def __init__(self, api_key: Optional[str] = None, use_openai: bool = False):
        self.use_openai = use_openai or bool(config.OPENAI_API_KEY and not config.ANTHROPIC_API_KEY)

        if self.use_openai:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or config.OPENAI_API_KEY)
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY)

    def generate_music_prompt(
        self,
        theme: str,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        language: Optional[str] = None,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        tempo: Optional[str] = None,
        sound_texture: Optional[str] = None,
        instrumental: bool = False
    ) -> dict:
        """
        주제를 기반으로 Suno용 프롬프트 생성

        Args:
            theme: 음악 주제 (예: "이별", "여름 바다", "새벽 감성")
            genre: 장르 (예: "K-pop", "R&B", "EDM") - 없으면 자동 선택
            mood: 분위기 (예: "신나는", "슬픈", "몽환적") - 없으면 자동 선택
            language: 가사 언어 (예: "Korean", "Japanese", "English") - 없으면 자동 선택
            gender: 보컬 성별 (예: "Male", "Female") - 없으면 자동 선택
            age: 보컬 나이 (예: "youthful", "mature", "aged") - 없으면 자동 선택
            tempo: 템포 (예: "very slow", "slow", "mid-tempo", "upbeat", "fast") - 없으면 자동 선택
            sound_texture: 사운드 질감 (예: "Clean", "Warm", "Dark", "Retro") - 없으면 자동 선택
            instrumental: True면 가사 없이 스타일만 생성

        Returns:
            {
                "title": "곡 제목",
                "style": "스타일 태그",
                "lyrics": "가사" (instrumental이면 빈 문자열)
            }
        """
        system_prompt = """당신은 Suno AI 음악 생성 전문가입니다.
사용자의 주제를 받아 Suno에서 좋은 결과가 나오는 프롬프트를 만들어주세요.

## 중요 규칙:
1. style 태그는 영어로 작성 (Suno가 영어 태그를 더 잘 이해함)
2. style에는 장르, 분위기, 악기, 보컬 스타일, 템포 등을 포함
3. 가사는 요청된 언어로 작성
4. 가사는 [Verse], [Chorus], [Bridge] 등의 구조 태그 사용
5. 제목은 요청된 언어로 작성
6. Please make sure the ending feels complete and emotionally resolved.

## style 태그 예시:
- "K-pop, energetic, synth, female vocal, catchy hook, 120bpm"
- "R&B, smooth, soulful, male vocal, romantic, piano"
- "Lo-fi, chill, dreamy, ambient, soft beats, rainy day"
- "EDM, upbeat, festival, drop, electronic, party anthem"
- "Ballad, emotional, orchestral, powerful vocal, heartfelt"

## 가사 구조 예시:
[Verse 1]
첫 번째 절 가사...

[Chorus]
후렴구 가사...

[Verse 2]
두 번째 절 가사...

[Bridge]
브릿지 가사...

[Outro]
아웃트로...

응답은 반드시 아래 JSON 형식으로만 해주세요:
{
    "title": "곡 제목",
    "style": "영어 스타일 태그들",
    "lyrics": "가사 (구조 태그 포함)"
}"""

        # 선택된 파라미터만 메시지에 포함
        conditions = [f"주제: {theme}"]
        conditions.append(f"장르: {genre if genre else '주제에 맞게 자동 선택'}")
        conditions.append(f"분위기: {mood if mood else '주제에 맞게 자동 선택'}")

        if language:
            conditions.append(f"가사 언어: {language}")
        else:
            conditions.append("가사 언어: 주제와 장르에 맞게 자동 선택 (한국어, 일본어, 영어 중)")

        if gender:
            conditions.append(f"보컬 성별: {gender}")
        if age:
            conditions.append(f"보컬 나이: {age}")
        if tempo:
            conditions.append(f"템포: {tempo}")
        if sound_texture:
            conditions.append(f"사운드 질감: {sound_texture}")

        conditions.append(f"인스트루멘탈: {'예 (가사 없이 스타일만)' if instrumental else '아니오 (가사 포함)'}")

        # 장르별 레퍼런스 프롬프트 추가
        genre_ref = ""
        if genre and genre in GENRE_REFERENCE:
            genre_ref = f"\n\n## 장르 레퍼런스 (style에 반드시 포함):\n{GENRE_REFERENCE[genre]}"

        user_message = f"""다음 조건으로 Suno 음악 프롬프트를 만들어주세요:

{chr(10).join(conditions)}{genre_ref}

JSON 형식으로만 응답해주세요."""

        # API 호출 (OpenAI 또는 Anthropic)
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            content = response.choices[0].message.content.strip()
        else:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            content = response.content[0].text.strip()

        # JSON 블록 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        import json
        result = json.loads(content)

        if instrumental:
            result["lyrics"] = ""

        return result

    def generate_batch_prompts(
        self,
        themes: list,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        language: str = "한국어",
        instrumental: bool = False
    ) -> list:
        """
        여러 주제에 대한 프롬프트 일괄 생성

        Args:
            themes: 주제 리스트
            나머지는 generate_music_prompt와 동일

        Returns:
            프롬프트 딕셔너리 리스트
        """
        results = []

        for theme in themes:
            try:
                prompt = self.generate_music_prompt(
                    theme=theme,
                    genre=genre,
                    mood=mood,
                    language=language,
                    instrumental=instrumental
                )
                prompt["theme"] = theme
                results.append(prompt)
            except Exception as e:
                results.append({
                    "theme": theme,
                    "error": str(e)
                })

        return results

    def generate_style_variations(
        self,
        base_theme: str,
        genres: list,
        language: str = "한국어"
    ) -> list:
        """
        하나의 주제로 여러 장르 버전 생성

        Args:
            base_theme: 기본 주제
            genres: 장르 리스트 (예: ["K-pop", "R&B", "Lo-fi"])
            language: 가사 언어

        Returns:
            각 장르별 프롬프트 리스트
        """
        results = []

        for genre in genres:
            try:
                prompt = self.generate_music_prompt(
                    theme=base_theme,
                    genre=genre,
                    language=language
                )
                results.append(prompt)
            except Exception as e:
                results.append({
                    "genre": genre,
                    "error": str(e)
                })

        return results

    def generate_random_themes(self, count: int = 10, category: Optional[str] = None) -> list:
        """
        랜덤 주제 생성

        Args:
            count: 생성할 주제 개수
            category: 카테고리 (예: "사랑", "일상", "계절") - 없으면 랜덤

        Returns:
            주제 문자열 리스트
        """
        system_prompt = """당신은 음악 주제 전문가입니다.
K-pop, 발라드, R&B 등 한국 음악에 어울리는 참신하고 감성적인 주제를 생성해주세요.
각 주제는 간결하게 2-5단어로 표현해주세요.

응답은 반드시 JSON 배열로만 해주세요:
["주제1", "주제2", "주제3", ...]"""

        user_message = f"""음악 주제 {count}개를 생성해주세요.
카테고리: {category if category else "다양하게 (사랑, 이별, 일상, 계절, 감정 등)"}

JSON 배열로만 응답해주세요."""

        # API 호출 (OpenAI 또는 Anthropic)
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            content = response.choices[0].message.content.strip()
        else:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            content = response.content[0].text.strip()

        # JSON 파싱
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        import json
        return json.loads(content)
