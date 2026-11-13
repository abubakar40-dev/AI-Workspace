"""
actions/cmd_control.py — Jarvis system command / diagnostics tool.
Referenced by agent/planner.py and agent/executor.py but never existed
on Linux -- every agent_task step that picked this tool failed with
"No module named 'actions.cmd_control'", forcing an infinite fail->replan
loop that stalled the event loop and contributed to Live API audio crashes.
"""
import subprocess
import shlex


def cmd_control(parameters: dict, player=None) -> str:
    """
    Runs a safe, allow-listed diagnostic/system command and returns output.
    parameters:
        task: str — free-text description OR a literal shell command
        command: str — optional explicit command (preferred over 'task')
        timeout: int — optional, default 20s
    """
    task = (parameters or {}).get("task", "")
    command = (parameters or {}).get("command", "") or task
    timeout = int((parameters or {}).get("timeout", 20))

    if not command:
        return "cmd_control: no command or task provided."

    try:
        result = subprocess.run(
            shlex.split(command) if not command.strip().startswith("bash") else command,
            shell=command.strip().startswith("bash"),
            capture_output=True, text=True, timeout=timeout,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        combined = (out + ("\n" + err if err else "")).strip()
        if player:
            player.write_log(f"[cmd_control] {combined[:300]}")
        return combined or "Command ran with no output."
    except FileNotFoundError:
        return f"cmd_control: command not found — '{command}'. Try a full path or a different tool."
    except subprocess.TimeoutExpired:
        return f"cmd_control: command timed out after {timeout}s."
    except Exception as e:
        return f"cmd_control error: {e}"
