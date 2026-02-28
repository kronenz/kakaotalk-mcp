"""Central configuration for KakaoTalk MCP Server."""
import os

# KakaoTalk window class names
KAKAO_MAIN_WINDOW_CLASS = "EVA_Window_Dblclk"
KAKAO_MAIN_WINDOW_TITLE = "카카오톡"
KAKAO_CHAT_WINDOW_CLASS = "EVA_Window_Dblclk"
KAKAO_LIST_CONTROL_CLASS = "EVA_VH_ListControl_Dblclk"
KAKAO_EDIT_CLASS = "RICHEDIT50W"

# Win32 message constants
WM_SETTEXT = 0x000C
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_A = 0x41
VK_C = 0x43
KEYEVENTF_KEYUP = 0x0002

# KakaoTalk data paths
KAKAO_LOCAL_DATA = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Kakao", "KakaoTalk"
)
KAKAO_USERS_DIR = os.path.join(KAKAO_LOCAL_DATA, "users")

# Image cache subdirectories to monitor
IMAGE_CACHE_SUBDIRS = [
    "chat_data/cli_http_v2",
    "chat_data/cli/thumbnail",
    "chat_data/oci_v2",
    "chat_data/mci_v2",
]

# Timeouts and intervals
CLIPBOARD_MAX_RETRIES = 5
CLIPBOARD_RETRY_INTERVAL_SEC = 0.1
KEY_COMBO_WAIT_SEC = 0.3

# Default output directory for downloaded images
DEFAULT_IMAGE_OUTPUT_DIR = os.path.join(
    os.environ.get("USERPROFILE", ""),
    "Documents", "KakaoMCP_Images"
)
