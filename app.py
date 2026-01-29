"""
Suno Automation - Streamlit UI
"""
import streamlit as st
import time
import random
from pathlib import Path

import config
from services.suno_client import SunoClient
from services.prompt_generator import PromptGenerator
from services.music_manager import MusicManager
from services.google_drive_manager import GoogleDriveManager

# 장르별 옵션 매핑
GENRE_OPTIONS = {
    "K-pop": {
        "tempo": ["mid-tempo", "upbeat", "fast"],
        "mood": ["신나는", "로맨틱", "강렬한"],
        "sound_texture": ["Clean", "Warm"]
    },
    "R&B": {
        "tempo": ["slow", "mid-tempo"],
        "mood": ["로맨틱", "우울한", "몽환적"],
        "sound_texture": ["Warm", "Dark"]
    },
    "Ballad": {
        "tempo": ["very slow", "slow"],
        "mood": ["슬픈", "로맨틱", "우울한"],
        "sound_texture": ["Warm", "Spacious"]
    },
    "EDM": {
        "tempo": ["upbeat", "fast"],
        "mood": ["신나는", "강렬한"],
        "sound_texture": ["Clean", "Dark"]
    },
    "Lo-fi": {
        "tempo": ["very slow", "slow"],
        "mood": ["편안한", "몽환적", "우울한"],
        "sound_texture": ["Minimal", "Warm"]
    },
    "Hip-hop": {
        "tempo": ["mid-tempo", "upbeat"],
        "mood": ["강렬한", "몽환적"],
        "sound_texture": ["Dark", "Clean"]
    },
    "Rock": {
        "tempo": ["mid-tempo", "fast"],
        "mood": ["강렬한", "신나는"],
        "sound_texture": ["Clean", "Dark"]
    },
    "Jazz": {
        "tempo": ["slow", "mid-tempo"],
        "mood": ["로맨틱", "편안한"],
        "sound_texture": ["Warm"]
    },
    "시티팝": {
        "tempo": ["mid-tempo", "upbeat", "slow"],
        "mood": ["로맨틱", "신나는", "몽환적"],
        "sound_texture": ["Warm", "Clean", "Retro", "Spacious"]
    },
    "클래식/OST": {
        "tempo": ["very slow", "slow", "mid-tempo"],
        "mood": ["슬픈", "웅장한", "몽환적"],
        "sound_texture": ["Spacious", "Dark"]
    }
}

# 시티팝 프리셋
CITYPOP_PRESETS = {
    "Stay With Me (Night City Pop)": {
        "style": "retro Japanese city pop style, 1980s inspired sound, mid-tempo groove, nostalgic night atmosphere, warm analog synths, smooth bass line, romantic and bittersweet mood, emotional female vocal, Japanese lyrics",
        "tempo": "mid-tempo",
        "mood": "로맨틱",
        "sound_texture": "Warm",
        "sound_texture_options": ["Warm"],
    },
    "Ride on Time (Drive City Pop)": {
        "style": "upbeat Japanese city pop style, 1980s inspired groove, driving rhythm, bright night city atmosphere, clean retro synths, funky bass line, energetic and uplifting mood, male or female vocal, Japanese lyrics",
        "tempo": "upbeat",
        "mood": "신나는",
        "sound_texture": "Clean",
        "sound_texture_options": ["Clean"],
    },
    "Windy Summer (Day City Pop)": {
        "style": "bright Japanese city pop style, 1980s pop inspired sound, mid-tempo rhythm, daytime city atmosphere, clean and warm synths, light groove, cheerful and romantic mood, female vocal, Japanese lyrics",
        "tempo": "mid-tempo",
        "mood": "로맨틱",
        "sound_texture": "Clean",
        "sound_texture_options": ["Clean", "Warm"],
    },
    "Blue Coral (Dream City Pop)": {
        "style": "dreamy Japanese city pop style, slow to mid-tempo, soft and floating atmosphere, blurred night memory mood, reverb-heavy synths, minimal rhythm, nostalgic and dreamy feeling, soft female vocal, Japanese lyrics",
        "tempo": "slow",
        "mood": "몽환적",
        "sound_texture": "Spacious",
        "sound_texture_options": ["Spacious"],
    },
}


# 페이지 설정
st.set_page_config(
    page_title="Suno Automation",
    page_icon="🎵",
    layout="wide"
)

# 세션 상태 초기화
if "suno_client" not in st.session_state:
    st.session_state.suno_client = None
if "prompt_generator" not in st.session_state:
    st.session_state.prompt_generator = None
if "drive_manager" not in st.session_state or st.session_state.drive_manager is None:
    st.session_state.drive_init_error = None
    # Google Drive Manager 초기화 (실패 시 재시도)
    if config.GOOGLE_DRIVE_ENABLED:
        try:
            # Streamlit Cloud: secrets에서 credentials 가져오기
            use_secrets = False
            try:
                if hasattr(st, 'secrets') and 'google_credentials' in st.secrets:
                    use_secrets = True
            except:
                pass  # secrets.toml 없으면 로컬 모드 사용

            if use_secrets:
                credentials_dict = dict(st.secrets['google_credentials'])
                folder_id = st.secrets.get('GOOGLE_DRIVE_FOLDER_ID', config.GOOGLE_DRIVE_FOLDER_ID)
                st.session_state.drive_manager = GoogleDriveManager(
                    folder_id=folder_id,
                    credentials_dict=credentials_dict
                )
            # 로컬: JSON 파일에서 credentials 가져오기
            else:
                st.session_state.drive_manager = GoogleDriveManager(
                    folder_id=config.GOOGLE_DRIVE_FOLDER_ID,
                    credentials_path=config.GOOGLE_CREDENTIALS_PATH
                )
            # 연결 실패 시 에러 저장
            if st.session_state.drive_manager and not st.session_state.drive_manager.is_connected():
                st.session_state.drive_init_error = "service=None (인증 실패)"
        except Exception as e:
            st.session_state.drive_manager = None
            st.session_state.drive_init_error = str(e)
    else:
        st.session_state.drive_manager = None
if "music_manager" not in st.session_state:
    st.session_state.music_manager = MusicManager(drive_manager=st.session_state.get("drive_manager"))
if "generated_songs" not in st.session_state:
    st.session_state.generated_songs = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "current_audio_url" not in st.session_state:
    st.session_state.current_audio_url = ""
if "current_audio_title" not in st.session_state:
    st.session_state.current_audio_title = ""
if "current_audio_id" not in st.session_state:
    st.session_state.current_audio_id = ""


def init_clients():
    """API 클라이언트 초기화"""
    if not config.SUNOAPI_KEY:
        return False, "SUNOAPI_KEY가 설정되지 않았습니다. (.env 파일 확인)"

    if not config.ANTHROPIC_API_KEY and not config.OPENAI_API_KEY:
        return False, "AI API 키가 설정되지 않았습니다. (Anthropic 또는 OpenAI)"

    try:
        st.session_state.suno_client = SunoClient()
        st.session_state.prompt_generator = PromptGenerator()
        return True, "연결 성공!"
    except Exception as e:
        return False, f"초기화 실패: {e}"


def main():
    st.title("🎵 Suno Automation")
    st.markdown("AI로 음악을 자동 생성하고 관리하세요")

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")

        # 연결 상태
        if st.button("🔌 API 연결", use_container_width=True):
            with st.spinner("연결 중..."):
                success, message = init_clients()
                if success:
                    st.success(message)
                    # 크레딧 정보 표시
                    try:
                        credits = st.session_state.suno_client.get_credits()
                        st.info(f"💳 크레딧: {credits['total_credits']}")
                    except Exception as e:
                        st.warning(f"크레딧 조회 실패: {e}")
                else:
                    st.error(message)

        # Google Drive 연결 상태
        if st.session_state.drive_manager and st.session_state.drive_manager.is_connected():
            st.success("☁️ Google Drive 연결됨")
        elif config.GOOGLE_DRIVE_ENABLED:
            st.warning("☁️ Google Drive 연결 실패")
        else:
            st.info("☁️ Google Drive 미설정")

        st.divider()

        # 통계
        st.header("📊 통계")
        stats = st.session_state.music_manager.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 생성", stats["total_generated"])
        with col2:
            st.metric("오늘", stats["today_count"])

        st.divider()

        # API 키 설정 도움말
        with st.expander("🔑 API 설정 방법"):
            st.markdown("""
**SunoAPI.org API 키:**
1. [sunoapi.org](https://sunoapi.org) 가입
2. API 키 발급
3. `.env` 파일의 `SUNOAPI_KEY`에 입력

**OpenAI API 키 (프롬프트 생성용):**
1. [OpenAI](https://platform.openai.com) 에서 API 키 발급
2. `.env` 파일의 `OPENAI_API_KEY`에 입력
            """)

    # 메인 탭
    tab1, tab2, tab3, tab4 = st.tabs(["🎹 음악 생성", "📚 생성 목록", "⚡ 대량 생성", "📥 내 라이브러리"])

    # 탭 1: 단일 음악 생성
    with tab1:
        st.header("단일 곡 생성")

        col1, col2 = st.columns(2)

        with col1:
            # 입력 모드 선택
            input_mode = st.radio(
                "입력 방식",
                ["주제만 입력 (AI가 프롬프트 생성)", "직접 입력"],
                horizontal=True
            )

            if input_mode == "주제만 입력 (AI가 프롬프트 생성)":
                theme = st.text_input("🎯 주제", placeholder="예: 이별 후 새로운 시작")

                # 장르 선택
                genre = st.selectbox(
                    "🎸 장르",
                    list(GENRE_OPTIONS.keys())
                )

                # 시티팝 프리셋 선택
                single_citypop_preset = None
                single_style_override = None
                if genre == "시티팝":
                    single_citypop_type = st.selectbox(
                        "🌃 시티팝 타입",
                        ["직접 설정"] + list(CITYPOP_PRESETS.keys()),
                        key="single_citypop_type"
                    )
                    if single_citypop_type != "직접 설정":
                        single_citypop_preset = CITYPOP_PRESETS[single_citypop_type]
                        single_style_override = single_citypop_preset["style"]

                # 장르 선택 시 해당 옵션만 드롭다운 표시
                if genre and genre in GENRE_OPTIONS:
                    genre_opts = GENRE_OPTIONS[genre]

                    if single_citypop_preset:
                        s_tempo_options = [single_citypop_preset["tempo"]]
                        s_mood_options = [single_citypop_preset["mood"]]
                        s_texture_options = single_citypop_preset["sound_texture_options"]
                    else:
                        s_tempo_options = genre_opts["tempo"]
                        s_mood_options = genre_opts["mood"]
                        s_texture_options = genre_opts["sound_texture"]

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        tempo = st.selectbox(
                            "⏱️ 템포",
                            s_tempo_options
                        )
                    with col_b:
                        mood = st.selectbox(
                            "🌈 분위기",
                            s_mood_options
                        )
                    with col_c:
                        sound_texture = st.selectbox(
                            "🔊 사운드 질감",
                            s_texture_options
                        )

                    col_d, col_e, col_f = st.columns(3)
                    with col_d:
                        language = st.selectbox(
                            "🌍 언어",
                            ["Korean", "Japanese", "English", "Korean + English", "Japanese + English"]
                        )
                    with col_e:
                        gender = st.selectbox(
                            "👤 성별",
                            ["Male", "Female"]
                        )
                    with col_f:
                        age = st.selectbox(
                            "🎤 보컬 나이",
                            ["youthful", "mature", "aged"]
                        )

                instrumental = st.checkbox("🎹 인스트루멘탈 (가사 없음)")

                if st.button("✨ 프롬프트 생성", use_container_width=True):
                    if not theme:
                        st.warning("주제를 입력해주세요")
                    elif not st.session_state.prompt_generator:
                        st.error("먼저 API를 연결해주세요")
                    else:
                        with st.spinner("프롬프트 생성 중..."):
                            try:
                                prompt_data = st.session_state.prompt_generator.generate_music_prompt(
                                    theme=theme,
                                    genre=genre,
                                    mood=mood,
                                    language=language,
                                    gender=gender,
                                    age=age,
                                    tempo=tempo,
                                    sound_texture=sound_texture,
                                    instrumental=instrumental
                                )
                                # 시티팝 프리셋이면 스타일 덮어쓰기
                                if single_style_override:
                                    prompt_data["style"] = single_style_override
                                st.session_state.current_prompt = prompt_data
                                st.success("프롬프트 생성 완료!")
                            except Exception as e:
                                st.error(f"프롬프트 생성 실패: {e}")

            else:  # 직접 입력
                title = st.text_input("🏷️ 제목", placeholder="곡 제목")
                style = st.text_input(
                    "🎨 스타일 태그",
                    placeholder="K-pop, energetic, female vocal, synth"
                )
                lyrics = st.text_area(
                    "📝 가사",
                    placeholder="[Verse 1]\n가사를 입력하세요...",
                    height=200
                )
                instrumental = st.checkbox("🎹 인스트루멘탈 (가사 없음)")

                if title or style:
                    st.session_state.current_prompt = {
                        "title": title,
                        "style": style,
                        "lyrics": "" if instrumental else lyrics,
                        "theme": title
                    }

        with col2:
            st.subheader("📋 현재 프롬프트")

            if "current_prompt" in st.session_state and st.session_state.current_prompt:
                prompt = st.session_state.current_prompt

                # 편집 가능
                edited_title = st.text_input("제목", value=prompt.get("title", ""))
                edited_style = st.text_input("스타일", value=prompt.get("style", ""))
                edited_lyrics = st.text_area("가사", value=prompt.get("lyrics", ""), height=150)

                st.session_state.current_prompt = {
                    **prompt,
                    "title": edited_title,
                    "style": edited_style,
                    "lyrics": edited_lyrics
                }

                st.divider()

                if st.button("🚀 음악 생성", type="primary", use_container_width=True):
                    if not st.session_state.suno_client:
                        st.error("먼저 API를 연결해주세요")
                    else:
                        generate_single_song(st.session_state.current_prompt)
            else:
                st.info("프롬프트를 생성하거나 직접 입력해주세요")

    # 탭 2: 생성 목록
    with tab2:
        st.header("생성된 음악 목록")

        songs = st.session_state.music_manager.get_recent_songs(50)

        if not songs:
            st.info("아직 생성된 음악이 없습니다")
        else:
            for song in songs:
                with st.expander(f"🎵 {song.get('title', 'Untitled')} - {song.get('created_at', '')[:10]}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**스타일:** {song.get('style', 'N/A')}")
                        st.write(f"**주제:** {song.get('theme', 'N/A')}")

                        if song.get("lyrics"):
                            st.markdown("**가사:**")
                            st.text(song["lyrics"])

                    with col2:
                        audio_url = song.get("audio_url", "")
                        audio_path = song.get("audio_path")

                        # 재생 버튼 (URL 또는 로컬 파일)
                        play_url = audio_url or ""
                        if play_url:
                            is_playing = (st.session_state.current_audio_url == play_url)
                            btn_label = "⏸️ 재생중" if is_playing else "▶️ 재생"
                            if st.button(btn_label, key=f"tab2_play_{song.get('id', '')}"):
                                if is_playing:
                                    st.session_state.current_audio_url = ""
                                    st.session_state.current_audio_title = ""
                                else:
                                    st.session_state.current_audio_url = play_url
                                    st.session_state.current_audio_title = song.get("title", "Untitled")
                                st.rerun()

                        if audio_path and Path(audio_path).exists():
                            with open(audio_path, "rb") as f:
                                st.download_button(
                                    "⬇️ 다운로드",
                                    data=f,
                                    file_name=Path(audio_path).name,
                                    mime="audio/mpeg"
                                )

    # 탭 3: 대량 생성
    with tab3:
        st.header("대량 음악 생성")

        st.warning("⚠️ Pro 플랜 기준 하루 약 100곡 (500 크레딧) 제한이 있습니다")

        col1, col2 = st.columns(2)

        with col1:
            batch_mode = st.radio(
                "생성 방식",
                ["주제 직접 입력", "AI가 랜덤 주제 생성"],
                horizontal=True
            )

            if batch_mode == "주제 직접 입력":
                themes_input = st.text_area(
                    "주제 목록 (한 줄에 하나씩)",
                    placeholder="이별의 아픔\n새벽 감성\n여름 바다\n첫사랑의 기억",
                    height=200
                )
                themes = [t.strip() for t in themes_input.split("\n") if t.strip()]
            else:
                num_themes = st.slider("생성할 곡 수", 1, 50, 10)
                category = st.selectbox(
                    "카테고리",
                    ["다양하게", "사랑/이별", "일상/감성", "계절/자연", "파티/신남"]
                )

                if st.button("🎲 주제 생성"):
                    if not st.session_state.prompt_generator:
                        st.error("먼저 API를 연결해주세요")
                    else:
                        with st.spinner("주제 생성 중..."):
                            try:
                                cat = None if category == "다양하게" else category
                                themes = st.session_state.prompt_generator.generate_random_themes(
                                    count=num_themes,
                                    category=cat
                                )
                                st.session_state.batch_themes = themes
                                st.success(f"{len(themes)}개 주제 생성 완료!")
                            except Exception as e:
                                st.error(f"주제 생성 실패: {e}")

                themes = st.session_state.get("batch_themes", [])

            st.write(f"**총 {len(themes)}개 주제**")
            if themes:
                for i, theme in enumerate(themes[:10], 1):
                    st.write(f"{i}. {theme}")
                if len(themes) > 10:
                    st.write(f"... 외 {len(themes) - 10}개")

        with col2:
            st.subheader("생성 설정")

            batch_genre = st.selectbox(
                "🎸 장르",
                list(GENRE_OPTIONS.keys()),
                key="batch_genre"
            )

            # 시티팝 프리셋 선택
            citypop_preset = None
            citypop_style_override = None
            if batch_genre == "시티팝":
                citypop_preset_name = st.selectbox(
                    "🌃 시티팝 타입",
                    ["직접 설정"] + list(CITYPOP_PRESETS.keys()),
                    key="batch_citypop_type"
                )
                if citypop_preset_name != "직접 설정":
                    citypop_preset = CITYPOP_PRESETS[citypop_preset_name]
                    citypop_style_override = citypop_preset["style"]

            # 장르에 맞는 옵션만 표시
            if batch_genre in GENRE_OPTIONS:
                batch_opts = GENRE_OPTIONS[batch_genre]

                if citypop_preset:
                    tempo_options = [citypop_preset["tempo"]]
                    mood_options = [citypop_preset["mood"]]
                    texture_options = citypop_preset["sound_texture_options"]
                else:
                    tempo_options = batch_opts["tempo"]
                    mood_options = batch_opts["mood"]
                    texture_options = batch_opts["sound_texture"]

                batch_tempo = st.selectbox(
                    "⏱️ 템포",
                    tempo_options,
                    key="batch_tempo"
                )

                batch_mood = st.selectbox(
                    "🌈 분위기",
                    mood_options,
                    key="batch_mood"
                )

                batch_sound_texture = st.selectbox(
                    "🔊 사운드 질감",
                    texture_options,
                    key="batch_sound_texture"
                )

            col_lang, col_gen, col_age = st.columns(3)
            with col_lang:
                batch_language = st.selectbox(
                    "🌍 언어",
                    ["Korean", "Japanese", "English", "Korean + English", "Japanese + English"],
                    key="batch_language"
                )
            with col_gen:
                batch_gender = st.selectbox(
                    "👤 성별",
                    ["Random", "Male", "Female"],
                    key="batch_gender"
                )
            with col_age:
                batch_age = st.selectbox(
                    "🎤 보컬 나이",
                    ["youthful", "mature", "aged"],
                    key="batch_age"
                )

            batch_instrumental = st.checkbox("🎹 인스트루멘탈", key="batch_inst")

            st.divider()

            # 스타일 프롬프트 미리보기
            if themes:
                if citypop_style_override:
                    style_preview = citypop_style_override
                else:
                    gender_display = "Male/Female (랜덤)" if batch_gender == "Random" else batch_gender
                    style_parts = [batch_genre, batch_mood, batch_sound_texture, f"{gender_display} vocal", batch_age, batch_tempo]
                    style_preview = ", ".join([p for p in style_parts if p])
                    if batch_instrumental:
                        style_preview += ", instrumental"
                st.caption("📋 스타일 프롬프트 미리보기")
                st.code(style_preview, language=None)

                estimated_credits = len(themes) * 10
                st.info(f"예상 크레딧 사용: {estimated_credits}")

            if st.button("🚀 대량 생성 시작", type="primary", use_container_width=True):
                if not themes:
                    st.warning("주제를 입력하거나 생성해주세요")
                elif not st.session_state.suno_client:
                    st.error("먼저 API를 연결해주세요")
                else:
                    generate_batch_songs(
                        themes=themes,
                        genre=batch_genre,
                        mood=batch_mood,
                        language=batch_language,
                        gender=batch_gender,
                        age=batch_age,
                        tempo=batch_tempo,
                        sound_texture=batch_sound_texture,
                        instrumental=batch_instrumental,
                        style_override=citypop_style_override
                    )

    # 탭 4: 이전 생성곡 다시 받기
    with tab4:
        # Artlist 스타일 CSS
        st.markdown("""
        <style>
            /* 라이브러리 탭 Artlist 스타일 */
            [data-testid="stVerticalBlock"] .library-header {
                display: flex;
                align-items: center;
                padding: 6px 12px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                font-size: 11px;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        </style>
        """, unsafe_allow_html=True)

        all_songs = sorted(
            st.session_state.music_manager.get_all_songs(),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )

        if not all_songs:
            st.info("이전에 생성한 곡이 없습니다.")
        else:
            missing_songs = [s for s in all_songs if not Path(s.get("audio_path", "")).exists()]

            # 상단 요약 + 전체 다운로드
            col_summary, col_dl_all = st.columns([3, 1])
            with col_summary:
                st.caption(f"총 {len(all_songs)}곡 · 미다운로드 {len(missing_songs)}곡")
            with col_dl_all:
                if missing_songs:
                    if st.button("📥 전체 다운로드", key="dl_all_btn", use_container_width=True):
                        download_all_missing(missing_songs)

            # 헤더 행
            h_play, h_title, h_style, h_dur, h_actions = st.columns([0.4, 2.5, 2, 0.6, 0.8])
            with h_title:
                st.caption("TITLE")
            with h_style:
                st.caption("STYLE")
            with h_dur:
                st.caption("TIME")

            # 곡 리스트
            for song in all_songs:
                render_library_song(song)



def refresh_audio_url(clip_id: str) -> str:
    """taskId를 사용해 sunoapi.org에서 새 오디오 URL 조회

    Args:
        clip_id: Suno 클립 ID

    Returns:
        새로운 audio_url (실패시 빈 문자열)
    """
    if not clip_id or not st.session_state.suno_client:
        return ""

    songs = st.session_state.music_manager.metadata["songs"]
    task_id = ""
    for s in songs:
        if s.get("id") == clip_id:
            task_id = s.get("task_id", "")
            break

    if not task_id:
        return ""

    try:
        status_data = st.session_state.suno_client._get_task_status(task_id)
        if status_data.get("status") != "SUCCESS":
            return ""

        response = status_data.get("response", {})
        suno_data = response.get("sunoData", [])

        for item in suno_data:
            if item.get("id") == clip_id:
                new_url = item.get("audioUrl") or item.get("sourceAudioUrl") or ""
                if new_url:
                    for s in songs:
                        if s.get("id") == clip_id:
                            s["audio_url"] = new_url
                            break
                    st.session_state.music_manager._save_metadata()
                return new_url

        return ""
    except Exception:
        return ""


def render_library_song(song: dict):
    """라이브러리 곡 렌더링 - Artlist 스타일"""
    title = song.get("title", "Untitled")
    created = song.get("created_at", "")[:10]
    audio_url = song.get("audio_url", "")
    clip_id = song.get("id", "")
    style = song.get("style", "")
    duration = song.get("duration", 0)
    lyrics = song.get("lyrics", "")
    audio_path = song.get("audio_path", "")
    has_local = Path(audio_path).exists()

    filename = st.session_state.music_manager.generate_filename(title, clip_id)
    library_path = config.LIBRARY_DIR / filename
    has_library = library_path.exists()

    is_playing = (st.session_state.current_audio_id == clip_id) if clip_id else False

    # Artlist 스타일 행: [▶] [Title/Date] [Style] [Duration] [Actions]
    col_play, col_title, col_style, col_dur, col_actions = st.columns([0.4, 2.5, 2, 0.6, 0.8])

    with col_play:
        play_icon = "⏸" if is_playing else "▶"
        if st.button(play_icon, key=f"play_{clip_id}", help=title):
            if is_playing:
                st.session_state.current_audio_id = ""
                st.session_state.current_audio_url = ""
                st.session_state.current_audio_title = ""
            else:
                # 로컬 파일 있으면 로컬 사용, 없으면 URL 갱신 시도
                if has_library or has_local:
                    play_url = audio_url
                else:
                    fresh_url = refresh_audio_url(clip_id)
                    play_url = fresh_url if fresh_url else ""
                st.session_state.current_audio_id = clip_id
                st.session_state.current_audio_url = play_url
                st.session_state.current_audio_title = title
            st.rerun()

    with col_title:
        if is_playing:
            st.markdown(f"**{title}**")
        else:
            st.markdown(f"{title}")
        st.caption(created)

    with col_style:
        if style:
            short_style = style[:40] + "..." if len(style) > 40 else style
            st.caption(short_style)

    with col_dur:
        if duration:
            minutes = int(float(duration)) // 60
            seconds = int(float(duration)) % 60
            st.caption(f"{minutes}:{seconds:02d}")

    has_task_id = bool(song.get("task_id", ""))

    with col_actions:
        a1, a2 = st.columns(2)
        with a1:
            if not has_local and not has_library and (audio_url or has_task_id):
                if st.button("⬇", key=f"dl_{clip_id}", help="다운로드"):
                    download_library_song(audio_url, title, clip_id)
            elif has_local or has_library:
                st.caption("✓")
        with a2:
            if lyrics:
                with st.popover("📝", help="가사"):
                    st.text(lyrics)

    # 재생중이면 오디오 플레이어 표시 (로컬 파일 우선)
    if is_playing:
        if has_library:
            st.audio(str(library_path))
        elif has_local:
            st.audio(audio_path)
        elif st.session_state.current_audio_url:
            st.audio(st.session_state.current_audio_url)
        else:
            st.caption("⚠️ URL 만료 - 재생 불가 (taskId 없음)")

    # 구분선 (얇게)
    st.markdown("<hr style='margin:0; border:none; border-top:1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)


def download_library_song(audio_url: str, title: str, clip_id: str):
    """라이브러리 곡 다운로드 (library 폴더에 저장, URL 만료시 taskId로 갱신)"""
    import requests as req
    try:
        with st.spinner("다운로드 중..."):
            filename = st.session_state.music_manager.generate_filename(title, clip_id)
            save_path = config.LIBRARY_DIR / filename

            response = None
            # 기존 URL로 시도
            if audio_url:
                response = req.get(audio_url, stream=True, timeout=60)

            # URL 만료시 (441 등) taskId로 갱신 시도
            if not response or response.status_code != 200:
                fresh_url = refresh_audio_url(clip_id)
                if fresh_url:
                    audio_url = fresh_url
                    response = req.get(audio_url, stream=True, timeout=60)

            if not response or response.status_code != 200:
                status = response.status_code if response else "N/A"
                st.error(f"다운로드 실패: HTTP {status} (URL 만료, 15일 이내 생성곡만 복구 가능)")
                return

            with open(str(save_path), "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            st.success(f"저장 완료: library/{save_path.name}")
    except Exception as e:
        st.error(f"다운로드 실패: {e}")


def download_all_missing(songs: list):
    """누락된 곡 전체 다운로드 (URL 만료시 taskId로 갱신)"""
    import requests as req
    total = len(songs)
    progress = st.progress(0, text=f"0/{total} 다운로드 중...")
    success = 0
    fail = 0

    for i, song in enumerate(songs):
        audio_url = song.get("audio_url", "")
        title = song.get("title", "Untitled")
        clip_id = song.get("id", "")

        if not audio_url and not song.get("task_id"):
            fail += 1
            continue

        try:
            filename = st.session_state.music_manager.generate_filename(title, clip_id)
            save_path = config.LIBRARY_DIR / filename

            if not save_path.exists():
                response = req.get(audio_url, stream=True, timeout=60) if audio_url else None

                # URL 만료시 taskId로 갱신 시도
                if not response or response.status_code != 200:
                    fresh_url = refresh_audio_url(clip_id)
                    if fresh_url:
                        audio_url = fresh_url
                        response = req.get(audio_url, stream=True, timeout=60)

                if response and response.status_code == 200:
                    with open(str(save_path), "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    success += 1
                else:
                    fail += 1
            else:
                success += 1  # 이미 존재
        except Exception:
            fail += 1

        progress.progress((i + 1) / total, text=f"{i + 1}/{total} 다운로드 중...")

    if fail > 0:
        st.warning(f"완료! 성공: {success}, 실패: {fail} (URL 만료된 곡은 taskId 없으면 복구 불가)")
    else:
        st.success(f"완료! {success}곡 다운로드 성공")


def generate_single_song(prompt_data: dict):
    """단일 곡 생성"""
    progress = st.progress(0, text="음악 생성 준비 중...")

    try:
        progress.progress(10, text="Suno에 요청 중...")

        clips = st.session_state.suno_client.generate(
            prompt=prompt_data.get("lyrics", ""),
            style=prompt_data.get("style", ""),
            title=prompt_data.get("title", ""),
            instrumental=not prompt_data.get("lyrics"),
            wait_for_completion=True
        )

        progress.progress(70, text="음악 다운로드 중...")

        for clip_index, clip in enumerate(clips):
            audio_url = clip.get("audio_url")
            if audio_url:
                # 파일 저장 (첫 번째=output1, 두 번째=output2)
                save_path = st.session_state.music_manager.get_audio_path(
                    prompt_data.get("title", "song"),
                    clip.get("id", ""),
                    clip_index=clip_index
                )

                save_path, audio_data = st.session_state.suno_client.download_audio(audio_url, str(save_path))

                # 메타데이터 저장
                st.session_state.music_manager.save_song(
                    clip_data=clip,
                    prompt_data=prompt_data,
                    audio_path=str(save_path),
                    audio_data=audio_data
                )

        progress.progress(100, text="완료!")
        st.success(f"🎉 {len(clips)}곡 생성 완료!")

        # 생성된 곡 재생
        for clip in clips:
            st.write(f"**{clip.get('title', 'Untitled')}**")
            audio_url = clip.get("audio_url")
            if audio_url:
                st.audio(audio_url)

    except Exception as e:
        st.error(f"생성 실패: {e}")


def generate_batch_songs(
    themes: list,
    genre: str = None,
    mood: str = None,
    language: str = None,
    gender: str = None,
    age: str = None,
    tempo: str = None,
    sound_texture: str = None,
    instrumental: bool = False,
    style_override: str = None
):
    """대량 곡 생성"""
    total = len(themes)
    progress = st.progress(0, text=f"0/{total} 생성 중...")
    status_container = st.empty()

    success_count = 0
    fail_count = 0

    for i, theme in enumerate(themes):
        # Random 선택시 곡마다 무작위 성별 적용
        current_gender = random.choice(["Male", "Female"]) if gender == "Random" else gender
        status_container.info(f"🎵 '{theme}' 생성 중... (성별: {current_gender})")

        try:
            # 프롬프트 생성
            prompt_data = st.session_state.prompt_generator.generate_music_prompt(
                theme=theme,
                genre=genre,
                mood=mood,
                language=language,
                gender=current_gender,
                age=age,
                tempo=tempo,
                sound_texture=sound_texture,
                instrumental=instrumental
            )
            prompt_data["theme"] = theme

            # 음악 생성 (시티팝 프리셋이면 style_override 사용)
            final_style = style_override if style_override else prompt_data.get("style", "")
            clips = st.session_state.suno_client.generate(
                prompt=prompt_data.get("lyrics", ""),
                style=final_style,
                title=prompt_data.get("title", ""),
                instrumental=instrumental,
                wait_for_completion=True
            )

            # 다운로드 및 저장 (첫 번째=output1, 두 번째=output2)
            for clip_index, clip in enumerate(clips):
                audio_url = clip.get("audio_url")
                if audio_url:
                    save_path = st.session_state.music_manager.get_audio_path(
                        prompt_data.get("title", "song"),
                        clip.get("id", ""),
                        clip_index=clip_index
                    )
                    save_path, audio_data = st.session_state.suno_client.download_audio(audio_url, str(save_path))
                    st.session_state.music_manager.save_song(
                        clip_data=clip,
                        prompt_data=prompt_data,
                        audio_path=str(save_path),
                        audio_data=audio_data
                    )

            success_count += 1

        except Exception as e:
            fail_count += 1
            status_container.error(f"'{theme}' 실패: {e}")
            time.sleep(1)

        progress.progress((i + 1) / total, text=f"{i + 1}/{total} 완료")

        # Rate limit 방지
        time.sleep(2)

    status_container.empty()
    st.success(f"🎉 완료! 성공: {success_count}, 실패: {fail_count}")




if __name__ == "__main__":
    main()
