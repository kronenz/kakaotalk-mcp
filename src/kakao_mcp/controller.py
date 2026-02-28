"""Win32 API wrapper for KakaoTalk PC automation."""
import os
import time
import ctypes
import shutil
from typing import Optional, List, Dict

import win32gui
import win32api
import win32con
import win32clipboard
import win32process

from . import config


# ---------------------------------------------------------------------------
# Window discovery
# ---------------------------------------------------------------------------

def is_kakaotalk_running() -> Dict:
    """Check if KakaoTalk main window exists.

    Returns:
        Dict with running (bool), hwnd (int|None), pid (int|None).
    """
    hwnd = win32gui.FindWindow(
        config.KAKAO_MAIN_WINDOW_CLASS, config.KAKAO_MAIN_WINDOW_TITLE
    )
    if hwnd == 0:
        return {"running": False, "hwnd": None, "pid": None}
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return {"running": True, "hwnd": hwnd, "pid": pid}


def find_chat_window(room_name: str) -> Optional[int]:
    """Find a chat window by exact title (room name).

    Returns hwnd or None.
    """
    results: List[int] = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if cls == config.KAKAO_CHAT_WINDOW_CLASS and title == room_name:
                results.append(hwnd)
        return True

    win32gui.EnumWindows(_cb, None)
    return results[0] if results else None


def list_chat_windows() -> List[Dict]:
    """List all currently open KakaoTalk chat windows.

    Returns list of dicts with hwnd and title.
    """
    main_hwnd = win32gui.FindWindow(
        config.KAKAO_MAIN_WINDOW_CLASS, config.KAKAO_MAIN_WINDOW_TITLE
    )
    windows: List[Dict] = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if (
                cls == config.KAKAO_CHAT_WINDOW_CLASS
                and hwnd != main_hwnd
                and title
                and title != config.KAKAO_MAIN_WINDOW_TITLE
            ):
                windows.append({"hwnd": hwnd, "title": title})
        return True

    win32gui.EnumWindows(_cb, None)
    return windows


def find_child_window_recursive(parent_hwnd: int, class_name: str) -> Optional[int]:
    """Recursively search for a child window by class name.

    Needed because RICHEDIT50W may be nested several levels deep.
    Returns hwnd or None.
    """
    found: List[int] = []

    def _cb(hwnd, _):
        if win32gui.GetClassName(hwnd) == class_name:
            found.append(hwnd)
            return False  # stop enumeration
        return True

    try:
        win32gui.EnumChildWindows(parent_hwnd, _cb, None)
    except Exception:
        pass
    return found[0] if found else None


def bring_window_to_front(hwnd: int):
    """Restore and bring a window to the foreground."""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)


# ---------------------------------------------------------------------------
# Keyboard helpers
# ---------------------------------------------------------------------------

_user32 = ctypes.windll.user32


def _send_ctrl_key_combo(vk_key: int):
    """Send Ctrl+<key> combo using keybd_event (requires foreground focus)."""
    _user32.keybd_event(config.VK_CONTROL, 0, 0, 0)
    time.sleep(0.02)
    _user32.keybd_event(vk_key, 0, 0, 0)
    time.sleep(0.02)
    _user32.keybd_event(vk_key, 0, config.KEYEVENTF_KEYUP, 0)
    time.sleep(0.02)
    _user32.keybd_event(config.VK_CONTROL, 0, config.KEYEVENTF_KEYUP, 0)


# ---------------------------------------------------------------------------
# Clipboard helpers
# ---------------------------------------------------------------------------

def _read_clipboard_text(max_retries: int = None, interval_sec: float = None) -> str:
    """Read text from clipboard with retry logic."""
    if max_retries is None:
        max_retries = config.CLIPBOARD_MAX_RETRIES
    if interval_sec is None:
        interval_sec = config.CLIPBOARD_RETRY_INTERVAL_SEC

    for _ in range(max_retries):
        try:
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                return data if data else ""
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            time.sleep(interval_sec)
    return ""


# ---------------------------------------------------------------------------
# Message sending
# ---------------------------------------------------------------------------

def send_message_to_room(room_name: str, text: str) -> Dict:
    """Send a text message to a KakaoTalk chat room.

    Uses WM_SETTEXT on RICHEDIT50W followed by VK_RETURN.
    The chat window must already be open.

    Returns:
        Dict with success (bool) and message or error.
    """
    hwnd = find_chat_window(room_name)
    if hwnd is None:
        return {"success": False, "error": f"Chat window '{room_name}' not found"}

    edit_hwnd = find_child_window_recursive(hwnd, config.KAKAO_EDIT_CLASS)
    if edit_hwnd is None:
        return {"success": False, "error": f"Edit control not found in '{room_name}'"}

    # Set text — SendMessageW handles Unicode (Korean) correctly
    win32api.SendMessage(edit_hwnd, config.WM_SETTEXT, 0, text)
    time.sleep(0.05)

    # Press Enter to send
    win32api.SendMessage(edit_hwnd, config.WM_KEYDOWN, config.VK_RETURN, 0)
    win32api.SendMessage(edit_hwnd, config.WM_KEYUP, config.VK_RETURN, 0)

    return {"success": True, "message": f"Message sent to '{room_name}'"}


# ---------------------------------------------------------------------------
# Message reading
# ---------------------------------------------------------------------------

def read_chat_messages(room_name: str) -> Dict:
    """Read messages from a KakaoTalk chat room via Ctrl+A → Ctrl+C.

    NOTE: This briefly brings the chat window to the foreground.

    Returns:
        Dict with success (bool), raw_text (str), and error if failed.
    """
    hwnd = find_chat_window(room_name)
    if hwnd is None:
        return {"success": False, "error": f"Chat window '{room_name}' not found", "raw_text": ""}

    list_hwnd = find_child_window_recursive(hwnd, config.KAKAO_LIST_CONTROL_CLASS)
    if list_hwnd is None:
        return {
            "success": False,
            "error": f"List control not found in '{room_name}'",
            "raw_text": "",
        }

    # Bring the chat window to foreground — required for keybd_event
    bring_window_to_front(hwnd)
    time.sleep(0.2)

    # Click on the list control to ensure it has focus
    try:
        rect = win32gui.GetWindowRect(list_hwnd)
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        _user32.SetCursorPos(cx, cy)
        _user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
        _user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
        time.sleep(0.1)
    except Exception:
        pass

    # Ctrl+A (select all)
    _send_ctrl_key_combo(config.VK_A)
    time.sleep(config.KEY_COMBO_WAIT_SEC)

    # Ctrl+C (copy)
    _send_ctrl_key_combo(config.VK_C)
    time.sleep(config.KEY_COMBO_WAIT_SEC)

    # Read clipboard
    raw_text = _read_clipboard_text()

    return {"success": True, "raw_text": raw_text}


# ---------------------------------------------------------------------------
# Room search/open
# ---------------------------------------------------------------------------

def search_and_open_room(room_name: str) -> Dict:
    """Search for a chat room in KakaoTalk main window and open it.

    Uses the search box (Ctrl+F equivalent) in the main window.

    Returns:
        Dict with success (bool) and message or error.
    """
    main_hwnd = win32gui.FindWindow(
        config.KAKAO_MAIN_WINDOW_CLASS, config.KAKAO_MAIN_WINDOW_TITLE
    )
    if main_hwnd == 0:
        return {"success": False, "error": "KakaoTalk main window not found"}

    bring_window_to_front(main_hwnd)
    time.sleep(0.3)

    # Find the search edit control in the main window
    edit_hwnd = find_child_window_recursive(main_hwnd, config.KAKAO_EDIT_CLASS)
    if edit_hwnd is None:
        return {"success": False, "error": "Search box not found in KakaoTalk main window"}

    # Clear and type room name
    win32api.SendMessage(edit_hwnd, config.WM_SETTEXT, 0, room_name)
    time.sleep(0.5)

    # Press Enter to open first search result
    win32api.SendMessage(edit_hwnd, config.WM_KEYDOWN, config.VK_RETURN, 0)
    win32api.SendMessage(edit_hwnd, config.WM_KEYUP, config.VK_RETURN, 0)
    time.sleep(0.5)

    # Clear search box with Escape
    win32api.SendMessage(edit_hwnd, config.WM_KEYDOWN, config.VK_ESCAPE, 0)
    win32api.SendMessage(edit_hwnd, config.WM_KEYUP, config.VK_ESCAPE, 0)

    # Verify the chat window opened
    time.sleep(0.3)
    new_hwnd = find_chat_window(room_name)
    if new_hwnd:
        return {"success": True, "message": f"Opened chat room '{room_name}'", "hwnd": new_hwnd}
    else:
        return {
            "success": False,
            "error": f"Chat room '{room_name}' not found after search. "
                     "The exact room name may differ from search results.",
        }


# ---------------------------------------------------------------------------
# Image download (cache-based)
# ---------------------------------------------------------------------------

def get_kakao_user_hash_dir() -> Optional[str]:
    """Find the first user hash directory under KakaoTalk users dir.

    KakaoTalk stores per-user data in a directory named with a SHA1 hash.
    Returns the full path or None.
    """
    users_dir = config.KAKAO_USERS_DIR
    if not os.path.isdir(users_dir):
        return None
    for entry in os.listdir(users_dir):
        full = os.path.join(users_dir, entry)
        if os.path.isdir(full) and len(entry) == 40:
            return full
    return None


def download_recent_images(
    room_name: str,
    output_dir: str,
    max_images: int = 10,
) -> Dict:
    """Download recent images from KakaoTalk cache.

    Collects image files from cache subdirectories sorted by modification time
    (newest first) and copies them to the output directory.

    Args:
        room_name: Chat room name (used for logging; cache is not per-room).
        output_dir: Directory to save images to.
        max_images: Max number of images to copy.

    Returns:
        Dict with message, images list, or error.
    """
    user_dir = get_kakao_user_hash_dir()
    if user_dir is None:
        return {"error": "KakaoTalk user data directory not found"}

    # Collect all image files from cache directories
    image_files: List[Dict] = []
    for subdir in config.IMAGE_CACHE_SUBDIRS:
        cache_path = os.path.join(user_dir, subdir)
        if not os.path.isdir(cache_path):
            continue
        for fname in os.listdir(cache_path):
            full_path = os.path.join(cache_path, fname)
            if not os.path.isfile(full_path):
                continue
            try:
                stat = os.stat(full_path)
                # Skip tiny files (< 1KB, likely not real images)
                if stat.st_size < 1024:
                    continue
                image_files.append({
                    "path": full_path,
                    "name": fname,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                })
            except OSError:
                continue

    if not image_files:
        return {
            "message": f"No cached images found for room '{room_name}'",
            "images": [],
        }

    # Sort by modification time (newest first)
    image_files.sort(key=lambda x: x["mtime"], reverse=True)
    image_files = image_files[:max_images]

    # Copy to output directory
    os.makedirs(output_dir, exist_ok=True)
    copied: List[Dict] = []
    for img in image_files:
        dest_name = img["name"]
        if not os.path.splitext(dest_name)[1]:
            dest_name += ".jpg"
        dest = os.path.join(output_dir, dest_name)
        try:
            shutil.copy2(img["path"], dest)
            copied.append({
                "source": img["path"],
                "destination": dest,
                "size": img["size"],
            })
        except OSError:
            continue

    return {
        "message": f"Downloaded {len(copied)} image(s) to {output_dir}",
        "images": copied,
    }
