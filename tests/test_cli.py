import os
import subprocess
import sys


def run_cli(*args, **kwargs):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("TYPESAFE_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    return subprocess.run([sys.executable, "-m", "scamshield", *args], env=env, capture_output=True, text=True, encoding="utf-8", **kwargs)


def test_offline_auto_keeps_state_across_turns():
    result = run_cli("--offline", "--auto")
    assert result.returncode == 0, result.stderr
    assert "OFFLINE" in result.stdout
    assert result.stdout.count("Jev Yes: 없음") == 1
    assert "통화 상태: 주의  점수: 10" in result.stdout
    assert "통화 상태: 위험  점수: 60" in result.stdout
    assert "[F1] risky" in result.stdout


def test_single_stt_text_without_yes_has_no_haiku_output():
    result = run_cli("--offline", "--text", "오늘 저녁에 만나요.")
    assert result.returncode == 0, result.stderr
    assert "통화 상태: 정상  점수: 0" in result.stdout
    assert "] uncertain" not in result.stdout and "] risky" not in result.stdout


def test_cli_sequential_input():
    result = run_cli("--offline", input="\n\n\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("입력 (Enter = 위 발화)") == 3


def test_live_mode_missing_key_does_not_silently_use_offline():
    result = run_cli("--text", "입력")
    assert result.returncode == 1
    assert "config/config" in result.stderr
    assert "TYPESAFE_API_KEY" in result.stderr


def test_empty_stt_text_and_conflicting_options():
    result = run_cli("--offline", "--text", " ")
    assert result.returncode == 1
    assert "INVALID_INPUT" in result.stderr
    assert run_cli("--offline", "--text", "입력", "--auto").returncode == 2


def test_chat_url_uses_supervisor_and_mock_tool():
    result = run_cli("--offline", "--chat", "https://safe-account-check.example/")
    assert result.returncode == 0, result.stderr
    assert "Supervisor 경로: url" in result.stdout
    assert "URL(Mock)" in result.stdout and "risky" in result.stdout
    assert "통화 상태:" not in result.stdout


def test_mixed_stt_and_url_runs_both_routes():
    result = run_cli("--offline", "--text", "송금하세요.", "--chat", "https://example.com/")
    assert result.returncode == 0, result.stderr
    assert "Supervisor 경로: call, url" in result.stdout
    assert "통화 상태: 위험" in result.stdout and "unknown" in result.stdout


def test_supervisor_auto_keeps_legacy_call_behavior():
    result = run_cli("--offline", "--supervisor", "--auto")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Supervisor 경로: call") == 3
    assert "통화 상태: 위험  점수: 60" in result.stdout
