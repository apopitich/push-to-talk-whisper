# Push-to-Talk Whisper

Push-to-talk voice input for Windows powered by Faster-Whisper with automatic text pasting and CUDA acceleration.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Why?

Lets you dictate text into any Windows application using a single hotkey.

- No cloud services
- No subscriptions
- Runs locally using Faster-Whisper
- CUDA acceleration on NVIDIA GPUs

## How it works

1. Hold `Ctrl+Alt+H`
2. Speak
3. Release
4. Text appears in the active field

Tray icon shows current state:

| Icon | State |
|---|---|
| Gray | Idle |
| Red | Recording |
| Yellow | Transcribing |

## Features

- GPU acceleration via CUDA (falls back to CPU if unavailable)
- Clipboard is restored after paste
- Focus returns to the source window after transcription
- VAD filter — ignores silence and background noise
- Max recording limit: 2 minutes

## Requirements

- Windows 10/11
- Python 3.11
- NVIDIA GPU recommended (falls back to CPU with `small` model)

## Installation

**1. Install Python 3.11**
```
winget install Python.Python.3.11
```

**2. Install FFmpeg**
```
winget install "FFmpeg (Essentials Build)"
```

**3. Install dependencies**
```
pip install -r requirements.txt
```

**5. Add NVIDIA library paths to PATH** (replace `YOUR_USER` with your username)
```powershell
$cudnnPath = "C:\Users\YOUR_USER\AppData\Local\Programs\Python\Python311\Lib\site-packages\nvidia\cudnn\bin"
$current = [Environment]::GetEnvironmentVariable("PATH", "User")
[Environment]::SetEnvironmentVariable("PATH", $current + ";$cudnnPath", "User")

$cublasPath = "C:\Users\YOUR_USER\AppData\Local\Programs\Python\Python311\Lib\site-packages\nvidia\cublas\bin"
$current = [Environment]::GetEnvironmentVariable("PATH", "User")
[Environment]::SetEnvironmentVariable("PATH", $current + ";$cublasPath", "User")
```
Restart terminal after this step.

## Usage

Run as administrator (administrator privileges may be required on some systems for global hotkeys):
```
pythonw voice_input.py
```

Right-click the tray icon → **Exit** to quit.

## Configuration

At the top of `voice_input.py`:

```python
HOTKEY = 'ctrl+alt+h'   # change to any hotkey
LANGUAGE = "ru"          # set to None for auto-detection
MODEL_NAME = "medium"    # small, medium, large-v3
MAX_DURATION = 120.0     # max recording length in seconds
```

## Autostart (optional)

Run in PowerShell as administrator:
```powershell
$action = New-ScheduledTaskAction -Execute "pythonw.exe" -Argument "C:\path\to\voice_input.py"
$trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
$trigger.Delay = "PT5M"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
Register-ScheduledTask -TaskName "Push-to-Talk Whisper" -Action $action -Trigger $trigger -Settings $settings -Principal $principal
```

## Desktop shortcut (optional)

Run in PowerShell as administrator:
```powershell
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Push-to-Talk Whisper.lnk")
$shortcut.TargetPath = (Get-Command pythonw.exe).Source
$shortcut.Arguments = "C:\path\to\voice_input.py"
$shortcut.WorkingDirectory = "C:\path\to\push-to-talk-whisper"
$shortcut.Save()
$bytes = [System.IO.File]::ReadAllBytes("$env:USERPROFILE\Desktop\VoicePaste.lnk")
$bytes[0x15] = $bytes[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes("$env:USERPROFILE\Desktop\VoicePaste.lnk", $bytes)
```

## License

MIT
