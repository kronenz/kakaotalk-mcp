# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-27

### Added

#### 기본 도구 (8개)
- `kakao_health_check` — 카카오톡 PC 실행 상태 확인 (윈도우 핸들, PID)
- `kakao_list_open_rooms` — 열려있는 채팅방 목록 조회
- `kakao_open_room` — 채팅방 검색 및 열기 (이미 열려있으면 포그라운드로)
- `kakao_send_message` — 채팅방에 메시지 전송 (클립보드 기반)
- `kakao_send_mention` — @멘션과 함께 메시지 전송 (한글 2벌식 키보드 시뮬레이션)
- `kakao_read_messages` — 채팅방 메시지 읽기 (Ctrl+A, Ctrl+C 클립보드 복사)
- `kakao_extract_links` — 채팅방에서 공유된 URL 추출
- `kakao_download_images` — 카카오톡 로컬 캐시에서 최근 이미지 다운로드

#### 모니터링 도구 (3개)
- `kakao_start_monitor` — 채팅방 키워드 모니터링 시작 (백그라운드 스레드)
- `kakao_stop_monitor` — 모니터링 중지
- `kakao_get_monitor_events` — 감지된 키워드 이벤트 조회 (트리거 메시지 + 최근 컨텍스트)

#### 인프라
- Win32 API 기반 카카오톡 PC 자동화 (`controller.py`)
- 카카오톡 클립보드 텍스트 파서 (`parser.py`)
- 한글 2벌식 자판 분해 및 키 입력 시뮬레이션 (초성/중성/종성 + 복합 자모)
- `pyproject.toml` 기반 패키지 구성 (`uvx kakaotalk-mcp` 실행 지원)
- 파서 단위 테스트 및 컨트롤러 mock 테스트 (28개)

### Fixed
- Windows 11에서 `SetForegroundWindow` 예외 처리
- 채팅방 검색 시 기존 검색어 잔류 문제 (ESC로 초기화)
- 메시지 전송 시 클립보드 충돌 방지 (`WM_SETTEXT` → 클립보드 `Ctrl+V` 방식)

[0.1.0]: https://github.com/kronenz/kakaotalk-mcp/releases/tag/v0.1.0
