# actions/reminder.py

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"


def _schedule_windows(target_dt: datetime, safe_message: str, task_name: str):
    """Original Windows Task Scheduler implementation. Returns an error string, or None on success."""
    python_exe = sys.executable
    if python_exe.lower().endswith("python.exe"):
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw

    temp_dir      = os.environ.get("TEMP", "C:\\Temp")
    notify_script = os.path.join(temp_dir, f"{task_name}.pyw")
    project_root  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    script_code = f'''import sys, os, time
sys.path.insert(0, r"{project_root}")

try:
    import winsound
    for freq in [800, 1000, 1200]:
        winsound.Beep(freq, 200)
        time.sleep(0.1)
except Exception:
    pass

try:
    from win10toast import ToastNotifier
    ToastNotifier().show_toast(
        "Jarvis Reminder",
        "{safe_message}",
        duration=15,
        threaded=False
    )
except Exception:
    try:
        import subprocess
        subprocess.run(["msg", "*", "/TIME:30", "{safe_message}"], shell=True)
    except Exception:
        pass

time.sleep(3)
try:
    os.remove(__file__)
except Exception:
    pass
'''
    with open(notify_script, "w", encoding="utf-8") as f:
        f.write(script_code)

    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Jarvis Reminder: {safe_message}</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>{target_dt.strftime("%Y-%m-%dT%H:%M:%S")}</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{notify_script}"</Arguments>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
</Task>'''

    xml_path = os.path.join(temp_dir, f"{task_name}.xml")
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml_content)

    result = subprocess.run(
        f'schtasks /Create /TN "{task_name}" /XML "{xml_path}" /F',
        shell=True, capture_output=True, text=True
    )

    try:
        os.remove(xml_path)
    except Exception:
        pass

    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        print(f"[Reminder] schtasks failed: {err}")
        try:
            os.remove(notify_script)
        except Exception:
            pass
        return "I couldn't schedule the reminder due to a system error."
    return None


def _schedule_linux(target_dt: datetime, safe_message: str, task_name: str):
    """
    Linux/macOS implementation. Prefers the `at` daemon (persists across reboots and
    doesn't need Jarvis to stay running). Falls back to a detached background process
    (setsid + sleep) that fires notify-send + a sound when `at`/atd isn't installed.
    Returns an error string, or None on success.
    """
    project_root  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    temp_dir      = "/tmp"
    notify_script = os.path.join(temp_dir, f"{task_name}.py")

    script_code = f'''import subprocess, shutil, os, sys
sys.path.insert(0, r"{project_root}")

msg = {safe_message!r}
title = "Jarvis Reminder"

if shutil.which("notify-send"):
    try:
        subprocess.run(["notify-send", title, msg], check=False)
    except Exception:
        pass

for player, args in (
    ("paplay", ["/usr/share/sounds/freedesktop/stereo/complete.oga"]),
    ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet",
                "/usr/share/sounds/freedesktop/stereo/complete.oga"]),
):
    if shutil.which(player):
        try:
            subprocess.run([player, *args], check=False,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except Exception:
            pass

try:
    os.remove(__file__)
except Exception:
    pass
'''
    with open(notify_script, "w", encoding="utf-8") as f:
        f.write(script_code)
    os.chmod(notify_script, 0o755)

    python_exe = sys.executable

    if shutil.which("at"):
        at_time = target_dt.strftime("%H:%M %m/%d/%Y")
        try:
            proc = subprocess.run(
                ["at", at_time],
                input=f'{python_exe} "{notify_script}"\n',
                capture_output=True, text=True,
            )
            if proc.returncode == 0:
                return None
        except Exception:
            pass

    # Fallback: detached background process that sleeps until the target time.
    delay_seconds = max(1, int((target_dt - datetime.now()).total_seconds()))
    try:
        subprocess.Popen(
            ["setsid", "bash", "-c", f'sleep {delay_seconds} && "{python_exe}" "{notify_script}"'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
        return None
    except Exception as e:
        return f"I couldn't schedule the reminder: {e}"


def reminder(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None
) -> str:
    """
    Sets a timed reminder.

    On Windows this uses Task Scheduler (original behavior).
    On Linux/macOS this uses the `at` daemon if available, otherwise a detached
    background process, and fires a desktop notification (+ sound) when due.

    parameters:
        - date    (str) YYYY-MM-DD
        - time    (str) HH:MM
        - message (str)

    Returns a result string — Live API voices it automatically.
    No edge_speak needed.
    """

    date_str = parameters.get("date")
    time_str = parameters.get("time")
    message  = parameters.get("message", "Reminder")

    if not date_str or not time_str:
        return "I need both a date and a time to set a reminder."

    try:
        target_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        if target_dt <= datetime.now():
            return "That time is already in the past."

        task_name    = f"JarvisReminder_{target_dt.strftime('%Y%m%d_%H%M')}"
        safe_message = message.replace('"', '').replace("'", "").strip()[:200]

        if _OS == "Windows":
            err = _schedule_windows(target_dt, safe_message, task_name)
        else:
            err = _schedule_linux(target_dt, safe_message, task_name)

        if err:
            return err

        if player:
            player.write_log(f"[reminder] set for {date_str} {time_str}")

        return f"Reminder set for {target_dt.strftime('%B %d at %I:%M %p')}."

    except ValueError:
        return "I couldn't understand that date or time format."

    except Exception as e:
        return f"Something went wrong while scheduling the reminder: {str(e)[:80]}"
