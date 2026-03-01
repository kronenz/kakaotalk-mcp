# KakaoTalk MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/platform-Windows-0078d4.svg)](https://www.microsoft.com/windows)

카카오톡 PC를 Win32 API로 제어하는 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 서버입니다.

Claude Desktop, Claude Code 등 MCP 클라이언트에서 카카오톡 메시지를 보내고, 읽고, 채팅방을 관리할 수 있습니다.

## 주요 기능

| 도구 | 설명 |
|------|------|
| `kakao_health_check` | 카카오톡 PC 실행 상태 확인 |
| `kakao_list_open_rooms` | 열려있는 채팅방 목록 조회 |
| `kakao_open_room` | 채팅방 검색 및 열기 |
| `kakao_send_message` | 채팅방에 메시지 전송 |
| `kakao_read_messages` | 채팅방 메시지 읽기 |
| `kakao_extract_links` | 채팅방에서 공유된 URL 추출 |
| `kakao_download_images` | 카카오톡 캐시에서 최근 이미지 다운로드 |

## 요구사항

- **Windows 10/11** (Win32 API 기반이므로 Windows 전용)
- **카카오톡 PC** 설치 및 로그인 상태
- **Python 3.10** 이상

## 설치

### uvx (권장)

별도 설치 없이 바로 실행:

```bash
uvx kakaotalk-mcp
```

### pip

```bash
pip install kakaotalk-mcp
```

### 소스에서 설치

```bash
git clone https://github.com/kronenz/kakaotalk-mcp.git
cd kakaotalk-mcp
pip install -e .
```

## 설정

### Claude Desktop

`%APPDATA%\Claude\claude_desktop_config.json` 파일에 추가:

**uvx 사용 시:**

```json
{
  "mcpServers": {
    "kakao": {
      "command": "uvx",
      "args": ["kakaotalk-mcp"]
    }
  }
}
```

**pip 설치 후:**

```json
{
  "mcpServers": {
    "kakao": {
      "command": "kakaotalk-mcp"
    }
  }
}
```

**소스에서 직접 실행:**

```json
{
  "mcpServers": {
    "kakao": {
      "command": "python",
      "args": ["C:/경로/kakaotalk-mcp/src/kakao_mcp/server.py"],
      "env": {
        "PYTHONPATH": "C:/경로/kakaotalk-mcp/src"
      }
    }
  }
}
```

### Claude Code

Claude Code 설정에서 MCP 서버 추가:

```bash
claude mcp add kakao -- uvx kakaotalk-mcp
```

또는 `.claude/settings.json`에 직접 추가:

```json
{
  "mcpServers": {
    "kakao": {
      "command": "uvx",
      "args": ["kakaotalk-mcp"]
    }
  }
}
```

## 사용 예시

Claude에게 자연어로 요청하면 됩니다:

- "카카오톡 실행 중인지 확인해줘"
- "열린 채팅방 목록 보여줘"
- "홍길동 채팅방 열어줘"
- "홍길동에게 '회의 10분 후에 시작합니다' 보내줘"
- "홍길동 채팅방 최근 대화 읽어줘"
- "홍길동 채팅방에서 공유된 링크 추출해줘"
- "최근 카카오톡 이미지 다운로드해줘"

## 제한사항 및 주의사항

- **Windows 전용**: Win32 API를 사용하므로 macOS/Linux에서는 동작하지 않습니다.
- **포그라운드 필요**: 메시지 읽기(`kakao_read_messages`)와 채팅방 열기(`kakao_open_room`) 시 카카오톡 창이 잠시 최전면으로 올라옵니다.
- **클립보드 사용**: 메시지 읽기/전송 시 시스템 클립보드를 사용합니다. 작업 중 클립보드 내용이 변경될 수 있습니다.
- **채팅방 이름 정확히 입력**: `kakao_send_message`, `kakao_read_messages`는 채팅방 창 제목이 정확히 일치해야 합니다. 먼저 `kakao_list_open_rooms`로 정확한 이름을 확인하세요.
- **이미지 다운로드**: 카카오톡 로컬 캐시에서 가져오며, 채팅방별 구분 없이 최근 캐시된 이미지가 다운로드됩니다.

## 프로젝트 구조

```
kakaotalk-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── requirements.txt
├── src/
│   └── kakao_mcp/
│       ├── __init__.py
│       ├── __main__.py      # python -m kakao_mcp 지원
│       ├── server.py        # MCP 서버 + 7개 도구 정의
│       ├── controller.py    # Win32 API 래퍼
│       ├── parser.py        # 클립보드 텍스트 파싱
│       └── config.py        # 상수 및 설정
└── tests/
    ├── test_parser.py       # 파서 단위 테스트
    └── test_controller.py   # 컨트롤러 mock 테스트
```

## 라이선스

[MIT License](LICENSE)
