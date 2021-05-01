import get_org_info
import pytest

def test_encoding_succeeds(capsys):
    """ Base64 encoding broke on move to py3 - make sure it stays fixed"""
    get_org_info.main()
    captured = capsys.readouterr()
    token = "MDEyOk9yZ2FuaXphdGlvbjEzMTUyNA=="  # nosec
    assert token in captured.out  # nosec
