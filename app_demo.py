"""
Suno Automation - 데모 버전 (API 연결 없이 UI만 미리보기)
"""
import streamlit as st
import time
from pathlib import Path


# 페이지 설정
st.set_page_config(
    page_title="Suno Automation (DEMO)",
    page_icon="🎵",
    layout="wide"
)

# 세션 상태 초기화
if "demo_songs" not in st.session_state:
    st.session_state.demo_songs = [
        {
            "id": "demo-1",
            "title": "새벽 감성",
            "style": "Lo-fi, chill, dreamy, soft piano, rainy day",
            "theme": "새벽에 혼자 듣는 감성",
            "lyrics": "[Verse 1]\n창밖에 비가 내려\n혼자 있는 이 밤\n\n[Chorus]\n새벽 감성에 젖어\n너를 떠올려",
            "created_at": "2025-01-20 10:30:00",
            "duration": 120,
        },
        {
            "id": "demo-2",
            "title": "Summer Party",
            "style": "EDM, upbeat, festival, energetic, summer vibes",
            "theme": "여름 파티",
            "lyrics": "[Verse 1]\nHands up in the air\nFeel the summer breeze\n\n[Chorus]\nLet's party all night long!",
            "created_at": "2025-01-20 09:15:00",
            "duration": 90,
        },
        {
            "id": "demo-3",
            "title": "첫사랑의 기억",
            "style": "K-pop ballad, emotional, piano, orchestra, female vocal",
            "theme": "첫사랑",
            "lyrics": "[Verse 1]\n그때 그 시절 우리\n손 잡고 걸었던 길\n\n[Chorus]\n아직도 기억나\n네 미소가",
            "created_at": "2025-01-19 22:00:00",
            "duration": 180,
        }
    ]


def main():
    # 데모 배너
    st.warning("🎮 **데모 모드** - API 연결 없이 UI만 미리보기입니다")

    st.title("🎵 Suno Automation")
    st.markdown("AI로 음악을 자동 생성하고 관리하세요")

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")

        # 연결 상태 (데모)
        if st.button("🔌 API 연결", use_container_width=True):
            with st.spinner("연결 중..."):
                time.sleep(1)
                st.success("연결 성공! (데모)")
                st.info("💳 크레딧: 450 / 500")

        st.divider()

        # 통계 (데모)
        st.header("📊 통계")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 생성", 127)
        with col2:
            st.metric("오늘", 15)

        st.divider()

        # 쿠키 설정 도움말
        with st.expander("🔑 Suno 쿠키 설정 방법"):
            st.markdown("""
1. [Suno](https://suno.com) 로그인
2. F12 → 개발자 도구 열기
3. Application 탭 → Cookies
4. `__session` 값 복사
5. `.env` 파일에 붙여넣기
            """)

    # 메인 탭
    tab1, tab2, tab3 = st.tabs(["🎹 음악 생성", "📚 생성 목록", "⚡ 대량 생성"])

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
                theme = st.text_input("🎯 주제", placeholder="예: 이별 후 새로운 시작", value="이별 후 새로운 시작")

                col_a, col_b = st.columns(2)
                with col_a:
                    genre = st.selectbox(
                        "🎸 장르",
                        ["자동 선택", "K-pop", "R&B", "Ballad", "EDM", "Lo-fi", "Hip-hop", "Rock", "Jazz", "시티팝", "팝", "클래식", "OST"]
                    )
                with col_b:
                    mood = st.selectbox(
                        "🌈 분위기",
                        ["자동 선택", "신나는", "슬픈", "몽환적", "편안한", "강렬한", "로맨틱", "우울한"]
                    )

                col_c, col_d = st.columns(2)
                with col_c:
                    language = st.selectbox(
                        "🌍 언어",
                        ["자동 선택", "Korean", "Japanese", "English", "Korean + English", "Japanese + English"]
                    )
                with col_d:
                    gender = st.selectbox(
                        "👤 성별",
                        ["자동 선택", "Male", "Female"]
                    )

                col_e, col_f = st.columns(2)
                with col_e:
                    age = st.selectbox(
                        "🎤 보컬 나이",
                        ["자동 선택", "youthful", "mature", "aged"]
                    )
                with col_f:
                    tempo = st.selectbox(
                        "⏱️ 템포",
                        ["자동 선택", "very slow", "slow", "mid-tempo", "upbeat", "fast"]
                    )

                sound_texture = st.selectbox(
                    "🔊 사운드 질감",
                    ["자동 선택", "Clean", "Warm", "Dark", "Retro", "Spacious", "Minimal"]
                )

                instrumental = st.checkbox("🎹 인스트루멘탈 (가사 없음)")

                if st.button("✨ 프롬프트 생성", use_container_width=True):
                    with st.spinner("프롬프트 생성 중..."):
                        time.sleep(1.5)
                        st.session_state.current_prompt = {
                            "title": "새로운 시작",
                            "style": "K-pop, hopeful, uplifting, synth, female vocal, inspirational",
                            "lyrics": """[Verse 1]
어두웠던 날들이 지나고
새로운 아침이 밝아와
눈물 닦고 일어서
다시 걸어가

[Chorus]
새로운 시작 새로운 나
두려움 없이 나아가
빛나는 내일을 향해
한 걸음씩 나아가""",
                            "theme": theme
                        }
                        st.success("프롬프트 생성 완료!")

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
                instrumental = st.checkbox("🎹 인스트루멘탈 (가사 없음)", key="direct_inst")

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
                    progress = st.progress(0, text="음악 생성 준비 중...")

                    time.sleep(0.5)
                    progress.progress(20, text="Suno에 요청 중...")
                    time.sleep(1)
                    progress.progress(50, text="음악 생성 중...")
                    time.sleep(1.5)
                    progress.progress(80, text="다운로드 중...")
                    time.sleep(0.5)
                    progress.progress(100, text="완료!")

                    st.success("🎉 2곡 생성 완료! (데모)")
                    st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
            else:
                st.info("프롬프트를 생성하거나 직접 입력해주세요")

    # 탭 2: 생성 목록
    with tab2:
        st.header("생성된 음악 목록")

        songs = st.session_state.demo_songs

        for song in songs:
            with st.expander(f"🎵 {song.get('title', 'Untitled')} - {song.get('created_at', '')[:10]}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**스타일:** {song.get('style', 'N/A')}")
                    st.write(f"**주제:** {song.get('theme', 'N/A')}")
                    st.write(f"**길이:** {song.get('duration', 0)}초")

                    if song.get("lyrics"):
                        st.markdown("**가사:**")
                        st.text(song["lyrics"])

                with col2:
                    st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
                    st.download_button(
                        "⬇️ 다운로드",
                        data=b"demo audio data",
                        file_name=f"{song['title']}.mp3",
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
                    value="이별의 아픔\n새벽 감성\n여름 바다\n첫사랑의 기억",
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
                    with st.spinner("주제 생성 중..."):
                        time.sleep(1)
                        st.session_state.batch_themes = [
                            "새벽 감성",
                            "비 오는 날의 커피",
                            "첫사랑의 기억",
                            "여름밤의 드라이브",
                            "혼자 있는 시간",
                            "다시 만난 우리",
                            "지나간 계절",
                            "별이 빛나는 밤",
                            "새로운 시작",
                            "너에게 보내는 편지"
                        ][:num_themes]
                        st.success(f"{len(st.session_state.batch_themes)}개 주제 생성 완료!")

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
                "장르 (전체 적용)",
                ["자동 선택", "K-pop", "R&B", "Ballad", "EDM", "Lo-fi", "Hip-hop", "Rock", "Jazz", "시티팝", "팝", "클래식", "OST"],
                key="batch_genre"
            )

            batch_language = st.selectbox(
                "언어 (전체 적용)",
                ["자동 선택", "Korean", "Japanese", "English", "Korean + English", "Japanese + English"],
                key="batch_language"
            )

            batch_gender = st.selectbox(
                "성별 (전체 적용)",
                ["자동 선택", "Male", "Female"],
                key="batch_gender"
            )

            batch_age = st.selectbox(
                "보컬 나이 (전체 적용)",
                ["자동 선택", "youthful", "mature", "aged"],
                key="batch_age"
            )

            batch_tempo = st.selectbox(
                "템포 (전체 적용)",
                ["자동 선택", "very slow", "slow", "mid-tempo", "upbeat", "fast"],
                key="batch_tempo"
            )

            batch_sound_texture = st.selectbox(
                "사운드 질감 (전체 적용)",
                ["자동 선택", "Clean", "Warm", "Dark", "Retro", "Spacious", "Minimal"],
                key="batch_sound_texture"
            )

            batch_instrumental = st.checkbox("인스트루멘탈", key="batch_inst")

            st.divider()

            # 예상 소요
            if themes:
                estimated_credits = len(themes) * 10
                st.info(f"예상 크레딧 사용: {estimated_credits}")

            if st.button("🚀 대량 생성 시작", type="primary", use_container_width=True):
                if not themes:
                    st.warning("주제를 입력하거나 생성해주세요")
                else:
                    progress = st.progress(0)
                    status = st.empty()

                    for i, theme in enumerate(themes):
                        status.info(f"🎵 '{theme}' 생성 중...")
                        time.sleep(0.5)
                        progress.progress((i + 1) / len(themes))

                    status.empty()
                    st.success(f"🎉 완료! 성공: {len(themes)}, 실패: 0 (데모)")


if __name__ == "__main__":
    main()
