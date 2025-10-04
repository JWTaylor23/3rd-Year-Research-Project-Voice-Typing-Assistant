"""

Voice Typing Assistant using speech recognition, text-to-speech, and tkinter for GUI.

Author: Joshua Taylor
Created: 20/11/2024
Last Updated: 04/10/2025
"""

__author__ = "Joshua Taylor"
__version__ = "1.1.0"

import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import pyautogui
import pyttsx3
import threading
import re

# Initialise speech engine and recogniser
engine = pyttsx3.init()
recogniser = sr.Recognizer()
mic = sr.Microphone()

# Global flags
is_listening = False
listening_thread = None


def speak(text: str):
    """
    The pyttsx3 library is used to speak the provided text aloud.
    """
    engine.say(text)
    engine.runAndWait()


def punctuate(text: str) -> str:
    """
    Replaces spoken punctuation keywords with symbols, case-insensitive,
    and normalizes spacing.
    """
    replacements = [
        (r'\bquestion mark\b', '?'),
        (r'\bexclamation mark\b', '!'),
        (r'\bcomma\b', ','),
        (r'\bfull stop\b', '.'),
        (r'\bnew line\b', '\n'),
    ]
    out = text
    for pattern, symbol in replacements:
        out = re.sub(pattern, symbol, out, flags=re.IGNORECASE)
    # Remove stray spaces before punctuation
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    return out.strip()


def auto_capitalise(text: str) -> str:
    """
    Capitalizes the first letter of each sentence while preserving spacing.
    Handles ., ?, ! as sentence terminals.
    """
    # Ensure a single space after terminal punctuation
    normalized = re.sub(r'\s*([.?!])\s*', r'\1 ', text).strip()
    parts = re.split(r'([.?!]\s)', normalized)  # keep delimiters
    out = []
    for i in range(0, len(parts), 2):
        sent = parts[i].strip()
        sep = parts[i + 1] if i + 1 < len(parts) else ''
        if sent:
            # manual capitalization to avoid lowercasing the rest
            sent = sent[0].upper() + sent[1:]
        out.append(sent + sep)
    return ''.join(out).strip()


def listen_and_type():
    """
    Listens for speech input, transcribes it, and types it via pyautogui.
    Exits promptly when is_listening is set to False.
    """
    global is_listening
    with mic as source:
        # Calibrate once at start
        recogniser.adjust_for_ambient_noise(source, duration=0.5)
        update_status("Listening... Speak now.")

        while is_listening:
            try:
                # Return periodically so it can be checked is_listening and UI stays responsive
                audio = recogniser.listen(source, timeout=1, phrase_time_limit=6)
            except sr.WaitTimeoutError:
                # No speech chunk started within timeout; loop to check flag
                continue

            try:
                text = recogniser.recognize_google(audio, language="en-GB")
            except sr.UnknownValueError:
                update_status("Didn't catch that. Try again.")
                continue
            except sr.RequestError:
                update_status("Could not connect to speech service (check internet).")
                # Bail out offline until network returns
                break

            # Post-processing
            if auto_punctuation.get():
                text = punctuate(text)
            if auto_capital.get():
                text = auto_capitalise(text)

            if text:
                append_output_line(text)
                try:
                    pyautogui.write(text, interval=0.05)
                except Exception as e:

                    update_status(f"Typing failed: {e}")
                    # Continue listening; the transcript still shows

    update_status("Stopped listening.")


def start_listening_thread():
    """
    The listening thread if it is not already running.

    """
    global is_listening, listening_thread
    if not is_listening:
        is_listening = True
        listening_thread = threading.Thread(target=listen_and_type, daemon=True)
        listening_thread.start()
        update_status("Started listening...")
    else:
        update_status("Already listening...")


def stop_listening():
    """
    Request the listening thread to stop and update UI.
    """
    global is_listening
    is_listening = False
    update_status("Stopping...")


def update_status(msg: str):
    """
    Thread-safe status update. Safe to call from any thread.
    """

    def _apply():
        status_label.config(text=msg)

    try:
        root.after(0, _apply)
    except RuntimeError:
        # root may be destroyed on shutdown
        pass


def append_output_line(line: str):
    """
    Thread-safe insert into the transcript box.
    """

    def _apply():
        output_box.insert(tk.END, line + '\n')
        output_box.see(tk.END)

    try:
        root.after(0, _apply)
    except RuntimeError:
        pass


def read_out_loud():
    """
    Allows the application to read out loud the transcribed text from the output box.
    """
    text = output_box.get("1.0", tk.END).strip()
    if text:
        speak(text)


# GUI setup
root = tk.Tk()
root.title("Voice Typing Assistant")
root.geometry("400x500")
root.resizable(False, False)

# GUI-bound tkinter variables
auto_punctuation = tk.BooleanVar(value=False)
auto_capital = tk.BooleanVar(value=True)

# UI Elements
title = ttk.Label(root, text="Voice Typing Assistant", font=("Arial", 16))
title.pack(pady=10)

start_btn = ttk.Button(root, text="Start Listening", command=start_listening_thread)
start_btn.pack(pady=5)

stop_btn = ttk.Button(root, text="Stop Listening", command=stop_listening)
stop_btn.pack(pady=5)

ttk.Checkbutton(root, text="Auto Capitalisation", variable=auto_capital).pack(pady=5)

read_btn = ttk.Button(root, text="Read Aloud", command=read_out_loud)
read_btn.pack(pady=5)

output_label = ttk.Label(root, text="Transcribed Output:")
output_label.pack()

output_box = tk.Text(root, height=8, width=45)
output_box.pack(pady=5)

status_label = ttk.Label(root, text="Ready", foreground="green")
status_label.pack(pady=10)

root.mainloop()
