"""Unit tests for submitter.should_skip_ai_suggest."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from submitter import should_skip_ai_suggest


def test_skip_ai_when_description_has_substantial_content():
    """Description co noi dung >5 chars -> skip AI goi y."""
    desc = "1. Background: x\n2. Objective: y\n3. Notes: z"
    assert should_skip_ai_suggest(desc) is True


def test_skip_ai_when_description_is_long_vietnamese():
    """Description tieng Viet dai -> skip AI."""
    desc = "1. Background: Toi can thong nhat scope voi team ve sprint moi nay"
    assert should_skip_ai_suggest(desc) is True


def test_dont_skip_when_description_empty():
    """Description rong -> can click AI goi y."""
    assert should_skip_ai_suggest("") is False


def test_dont_skip_when_description_none():
    """Description None -> can click AI goi y."""
    assert should_skip_ai_suggest(None) is False


def test_dont_skip_when_description_only_whitespace():
    """Description chi co whitespace -> can click AI."""
    assert should_skip_ai_suggest("   \n\t  ") is False


def test_dont_skip_when_description_too_short():
    """Description ngan (<=5 chars) -> can click AI goi y (khong du chat luong)."""
    assert should_skip_ai_suggest("abc") is False
    assert should_skip_ai_suggest("12345") is False
