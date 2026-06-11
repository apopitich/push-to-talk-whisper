import os
import site
import threading
import time

for pkg in site.getsitepackages():
    for lib in ["nvidia\\cudnn\\bin", "nvidia\\cublas\\bin"]:
        path = os.path.join(pkg, lib)
        if os.path.isdir(path):
            os.add_dll_directory(path)
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd
import pyperclip
import keyboard
import pystray
import win32gui
from PIL import Image, ImageDraw

__version__ = "1.0.0"

HOTKEY = 'ctrl+alt+h'
LANGUAGE = "ru"       # set to None for auto-detection
MODEL_NAME = "medium" # small, medium, large-v3
SAMPLE_RATE = 16000
MIN_DURATION = 0.5
MAX_DURATION = 120.0
MAX_SAMPLES = int(MAX_DURATION * SAMPLE_RATE)

try:
    model = WhisperModel(MODEL_NAME, device="cuda", compute_type="float16")
except Exception:
    model = WhisperModel("small", device="cpu", compute_type="int8")

IDLE = 'idle'
RECORDING = 'recording'
PROCESSING = 'processing'

state = IDLE
state_lock = threading.Lock()
recording_event = threading.Event()
audio_chunks = []
audio_samples_count = 0
audio_lock = threading.Lock()
process_event = threading.Event()
tray_icon = None
source_hwnd = None

def make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, 63, 63], fill=(40, 40, 40, 255))
    d.rounded_rectangle([22, 8, 42, 38], radius=10, fill=color)
    d.arc([14, 24, 50, 52], start=0, end=180, fill=color, width=3)
    d.line([32, 52, 32, 58], fill=color, width=3)
    d.line([24, 58, 40, 58], fill=color, width=3)
    return img

def set_tray(color, title):
    if tray_icon:
        tray_icon.icon = make_icon(color)
        tray_icon.title = title

def quit_app(icon, item):
    stream.stop()
    stream.close()
    keyboard.unhook_all()
    icon.stop()
    os._exit(0)

def audio_callback(indata, frames, time_info, status):
    global audio_samples_count
    if not recording_event.is_set():
        return
    with audio_lock:
        if audio_samples_count < MAX_SAMPLES:
            audio_chunks.append(indata.copy())
            audio_samples_count += len(indata)
        elif audio_samples_count == MAX_SAMPLES:
            audio_samples_count += 1
            if tray_icon:
                tray_icon.notify("2-minute limit reached. Release the key.", "Push-to-Talk Whisper")

try:
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
    stream.start()
except Exception as e:
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, f"Microphone error: {e}", "Push-to-Talk Whisper", 0)
    os._exit(1)

def on_key(e):
    global state, source_hwnd, audio_samples_count
    if e.name != 'h':
        return
    if e.event_type == keyboard.KEY_DOWN:
        if not (keyboard.is_pressed('ctrl') and keyboard.is_pressed('alt')):
            return
        with state_lock:
            if state != IDLE:
                return
            state = RECORDING
        source_hwnd = win32gui.GetForegroundWindow()
        with audio_lock:
            audio_chunks.clear()
            audio_samples_count = 0
        recording_event.set()
        set_tray("red", "Recording...")
    elif e.event_type == keyboard.KEY_UP:
        with state_lock:
            if state != RECORDING:
                return
            state = PROCESSING
        recording_event.clear()
        process_event.set()

keyboard.hook(on_key, suppress=False)
keyboard.add_hotkey('ctrl+alt+h', lambda: None, suppress=True)

def main_loop():
    global state, audio_samples_count
    while True:
        process_event.wait()
        process_event.clear()
        with audio_lock:
            chunks = list(audio_chunks)
            audio_chunks.clear()
            audio_samples_count = 0
        if not chunks:
            with state_lock:
                state = IDLE
            set_tray("gray", f"Push-to-Talk Whisper — {HOTKEY}")
            continue
        audio = np.concatenate(chunks).flatten()
        duration = len(audio) / SAMPLE_RATE
        if duration < MIN_DURATION:
            with state_lock:
                state = IDLE
            set_tray("gray", f"Push-to-Talk Whisper — {HOTKEY}")
            continue
        try:
            set_tray("yellow", "Transcribing...")
            segments, _ = model.transcribe(
                audio,
                language=LANGUAGE,
                vad_filter=True
            )
            text = "".join(s.text for s in segments).strip()
            if text:
                old_clip = ""
                try:
                    old_clip = pyperclip.paste()
                except Exception:
                    pass
                try:
                    pyperclip.copy(text)
                    if source_hwnd and win32gui.IsWindow(source_hwnd):
                        try:
                            win32gui.SetForegroundWindow(source_hwnd)
                        except Exception:
                            pass
                    time.sleep(0.1)
                    keyboard.send('ctrl+v')
                    time.sleep(0.5)
                finally:
                    try:
                        pyperclip.copy(old_clip)
                    except Exception:
                        pass
            else:
                if tray_icon:
                    tray_icon.notify("No speech detected", "Push-to-Talk Whisper")
        except Exception as ex:
            if tray_icon:
                tray_icon.notify(str(ex), "Push-to-Talk Whisper: error")
        finally:
            with state_lock:
                state = IDLE
            set_tray("gray", f"Push-to-Talk Whisper — {HOTKEY}")

threading.Thread(target=main_loop, daemon=True).start()

tray_icon = pystray.Icon(
    "Push-to-Talk Whisper",
    make_icon("gray"),
    f"Push-to-Talk Whisper — {HOTKEY}",
    menu=pystray.Menu(pystray.MenuItem("Exit", quit_app))
)
tray_icon.run()
