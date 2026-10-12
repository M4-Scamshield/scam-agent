import subprocess
import sys


def test_offline_cli_auto():
    result = subprocess.run([sys.executable, "-m", "scamshield", "--offline", "--auto"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for marker in ("OFFLINE", "[verify_agent]", "[tool_execution]", "phase=VERIFY", "phase=WARN", "통화 누적: 대화 3개 / 조회 1개", '"is_mock": true'):
        assert marker in result.stdout
    assert result.stdout.count("[tool_execution]") == 1


def test_cli_sequential_input():
    result = subprocess.run([sys.executable, "-m", "scamshield", "--offline"], input="\n\n\n", capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("입력 (Enter = 위 발화)") == 3
    assert "phase=WARN risk=0.9" in result.stdout
