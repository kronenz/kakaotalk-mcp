"""Mock-based unit tests for kakao_mcp.controller."""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kakao_mcp import controller, config


# ---------------------------------------------------------------------------
# is_kakaotalk_running
# ---------------------------------------------------------------------------

@patch("kakao_mcp.controller.win32process")
@patch("kakao_mcp.controller.win32gui")
def test_is_running_true(mock_gui, mock_proc):
    mock_gui.FindWindow.return_value = 12345
    mock_proc.GetWindowThreadProcessId.return_value = (0, 9876)
    result = controller.is_kakaotalk_running()
    assert result["running"] is True
    assert result["hwnd"] == 12345
    assert result["pid"] == 9876
    mock_gui.FindWindow.assert_called_once_with(
        config.KAKAO_MAIN_WINDOW_CLASS, config.KAKAO_MAIN_WINDOW_TITLE
    )


@patch("kakao_mcp.controller.win32gui")
def test_is_running_false(mock_gui):
    mock_gui.FindWindow.return_value = 0
    result = controller.is_kakaotalk_running()
    assert result["running"] is False
    assert result["hwnd"] is None


# ---------------------------------------------------------------------------
# find_chat_window
# ---------------------------------------------------------------------------

@patch("kakao_mcp.controller.win32gui")
def test_find_chat_window_found(mock_gui):
    # Simulate EnumWindows calling the callback with a matching window
    def enum_side_effect(callback, _):
        # Simulate a matching window
        mock_gui.IsWindowVisible.return_value = True
        mock_gui.GetClassName.return_value = config.KAKAO_CHAT_WINDOW_CLASS
        mock_gui.GetWindowText.return_value = "TestRoom"
        callback(99999, None)

    mock_gui.EnumWindows.side_effect = enum_side_effect
    result = controller.find_chat_window("TestRoom")
    assert result == 99999


@patch("kakao_mcp.controller.win32gui")
def test_find_chat_window_not_found(mock_gui):
    def enum_side_effect(callback, _):
        mock_gui.IsWindowVisible.return_value = True
        mock_gui.GetClassName.return_value = config.KAKAO_CHAT_WINDOW_CLASS
        mock_gui.GetWindowText.return_value = "OtherRoom"
        callback(99999, None)

    mock_gui.EnumWindows.side_effect = enum_side_effect
    result = controller.find_chat_window("TestRoom")
    assert result is None


# ---------------------------------------------------------------------------
# list_chat_windows
# ---------------------------------------------------------------------------

@patch("kakao_mcp.controller.win32gui")
def test_list_chat_windows(mock_gui):
    mock_gui.FindWindow.return_value = 10000  # main window

    call_count = [0]
    rooms_data = [
        (10000, config.KAKAO_MAIN_WINDOW_TITLE),  # main window — should be excluded
        (20001, "Room A"),
        (20002, "Room B"),
    ]

    def enum_side_effect(callback, _):
        for hwnd, title in rooms_data:
            mock_gui.IsWindowVisible.return_value = True
            mock_gui.GetClassName.return_value = config.KAKAO_CHAT_WINDOW_CLASS
            mock_gui.GetWindowText.return_value = title
            callback(hwnd, None)

    mock_gui.EnumWindows.side_effect = enum_side_effect
    result = controller.list_chat_windows()
    titles = [r["title"] for r in result]
    assert "Room A" in titles
    assert "Room B" in titles
    assert config.KAKAO_MAIN_WINDOW_TITLE not in titles


# ---------------------------------------------------------------------------
# send_message_to_room
# ---------------------------------------------------------------------------

@patch("kakao_mcp.controller.win32api")
@patch("kakao_mcp.controller.find_child_window_recursive")
@patch("kakao_mcp.controller.find_chat_window")
def test_send_message_success(mock_find, mock_child, mock_api):
    mock_find.return_value = 11111
    mock_child.return_value = 22222
    result = controller.send_message_to_room("TestRoom", "Hello")
    assert result["success"] is True
    assert "sent" in result["message"].lower()


@patch("kakao_mcp.controller.find_chat_window")
def test_send_message_room_not_found(mock_find):
    mock_find.return_value = None
    result = controller.send_message_to_room("NoRoom", "Hello")
    assert result["success"] is False
    assert "not found" in result["error"]


@patch("kakao_mcp.controller.find_child_window_recursive")
@patch("kakao_mcp.controller.find_chat_window")
def test_send_message_no_edit_control(mock_find, mock_child):
    mock_find.return_value = 11111
    mock_child.return_value = None
    result = controller.send_message_to_room("TestRoom", "Hello")
    assert result["success"] is False
    assert "edit control" in result["error"].lower()


# ---------------------------------------------------------------------------
# read_chat_messages
# ---------------------------------------------------------------------------

@patch("kakao_mcp.controller._read_clipboard_text")
@patch("kakao_mcp.controller._send_ctrl_key_combo")
@patch("kakao_mcp.controller._user32")
@patch("kakao_mcp.controller.win32gui")
@patch("kakao_mcp.controller.find_child_window_recursive")
@patch("kakao_mcp.controller.find_chat_window")
def test_read_messages_success(mock_find, mock_child, mock_gui, mock_user32, mock_ctrl, mock_clip):
    mock_find.return_value = 11111
    mock_child.return_value = 33333
    mock_gui.GetWindowRect.return_value = (0, 0, 100, 100)
    mock_clip.return_value = "[Room] [대화상대 2명]\n[A] [오전 10:00] Hello"
    result = controller.read_chat_messages("Room")
    assert result["success"] is True
    assert "Hello" in result["raw_text"]


@patch("kakao_mcp.controller.find_chat_window")
def test_read_messages_room_not_found(mock_find):
    mock_find.return_value = None
    result = controller.read_chat_messages("NoRoom")
    assert result["success"] is False


# ---------------------------------------------------------------------------
# get_kakao_user_hash_dir
# ---------------------------------------------------------------------------

@patch("os.listdir")
@patch("os.path.isdir")
def test_get_user_hash_dir_found(mock_isdir, mock_listdir):
    mock_isdir.return_value = True
    mock_listdir.return_value = ["a" * 40, "not_a_hash"]

    # Make only the 40-char entry look like a directory
    def isdir_side(path):
        return True

    mock_isdir.side_effect = isdir_side
    result = controller.get_kakao_user_hash_dir()
    assert result is not None
    assert "a" * 40 in result


@patch("os.path.isdir")
def test_get_user_hash_dir_no_users_dir(mock_isdir):
    mock_isdir.return_value = False
    result = controller.get_kakao_user_hash_dir()
    assert result is None
