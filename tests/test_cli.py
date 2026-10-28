import os
import subprocess
import sys


def run_cli(*args, **kwargs):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("TYPESAFE_API_KEY", None)
    env.pop("GEMINI_API_KEY", None)
    return subprocess.run([sys.executable, "-m", "scamshield", *args], env=env, capture_output=True, text=True, encoding="utf-8", **kwargs)


def test_offline_auto_shows_no_and_yes_routes():
    result = run_cli("--offline", "--auto")
    assert result.returncode == 0, result.stderr
    assert "OFFLINE" in result.stdout
    assert "verdict=No" in result.stdout
    assert "verdict=Yes" in result.stdout
    assert result.stdout.count("[detect_with_jev]") == 3
    assert result.stdout.count("[respond_with_llm]") == 2
    assert "통화 누적: 대화 3개" in result.stdout


def test_single_stt_text_no_has_no_llm_output():
    result = run_cli("--offline", "--text", "오늘 저녁에 만나요.")
    assert result.returncode == 0, result.stderr
    assert '"analysis": null' in result.stdout
    assert "[respond_with_llm]" not in result.stdout


def test_cli_sequential_input():
    result = run_cli("--offline", input="\n\n\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("입력 (Enter = 위 발화)") == 3


def test_live_mode_missing_key_does_not_silently_use_offline():
    result = run_cli("--text", "입력")
    assert result.returncode == 1
    assert "MISSING_API_KEY" in result.stderr


def test_empty_stt_text_and_conflicting_options():
    result = run_cli("--offline", "--text", " ")
    assert result.returncode == 1
    assert "INVALID_INPUT" in result.stdout
    assert run_cli("--offline", "--text", "입력", "--auto").returncode == 2
