"""
Jarvis Voice Assistant — Voice-to-Voice Edition
-----------------------------------------------
✅ Wake word detection ("Jarvis")
✅ Whisper for speech recognition
✅ AI chat (Phi-3 mini)
✅ Edge-TTS for natural speech output
✅ Can open sites and apps
"""

from __future__ import annotations
import os
import time
import struct
import webbrowser
import asyncio
import pyaudio
import sounddevice as sd
from datetime import datetime
from faster_whisper import WhisperModel
from transformers import pipeline
import pvporcupine
import requests
import edge_tts  # 👈 Microsoft neural voice


class JarvisDaemon:
    def __init__(self):
        print("🚀 Initializing Jarvis Voice Assistant...")
        self.whisper = WhisperModel("base", device="cpu")

        # Try local AI
        try:
            print("🧠 Loading local AI model (Phi-3-mini)...")
            self.ai = pipeline(
                "text-generation",
                model="microsoft/Phi-3-mini-4k-instruct",
                device="cpu",
            )
            self.use_local_ai = True
            print("✅ Local AI ready.")
        except Exception as e:
            print(f"⚠️ Local AI failed: {e}. Switching to online AI.")
            self.use_local_ai = False

        # Wake word setup
        access_key = "cLMLLwKUgjq8FqiG6xp74jElkFpPbcdjwPruG9v2TX0we9b+2XZAKg=="
        self.porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
        )

        self.running = True
        print("🎙️ Listening for 'Jarvis'...")

    # -----------------------------
    # VOICE OUTPUT
    # -----------------------------
    async def speak(self, text: str):
        """Convert text to realistic voice using Microsoft Edge TTS."""
        if not text.strip():
            return
        print(f"Jarvis 🗣️: {text}")
        voice = "en-US-GuyNeural"  # You can change to "en-US-JennyNeural"
        file_path = "jarvis_response.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file_path)
        os.system(f'start /min wmplayer "{file_path}"')  # play via Windows Media Player silently

    # -----------------------------
    # VOICE INPUT
    # -----------------------------
    def transcribe(self, duration=4):
        """Listen and convert your speech to text."""
        print("🎧 Listening for your command (4 sec)...")
        audio_data = sd.rec(
            int(duration * 16000),
            samplerate=16000,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        try:
            segments, _ = self.whisper.transcribe(audio_data.flatten())
            text = " ".join([s.text for s in segments]).strip()
        except Exception as e:
            print(f"⚠️ Transcription error: {e}")
            text = ""
        print(f"🗣️ You said: {text}")
        return text.lower()

    # -----------------------------
    # AI RESPONSE
    # -----------------------------
    def ask_ai(self, query: str) -> str:
        if not query:
            return "Sorry, I didn’t hear you."

        if self.use_local_ai:
            try:
                result = self.ai(query, max_new_tokens=60)[0]["generated_text"]
                return result.strip()
            except Exception as e:
                print(f"⚠️ Local AI error: {e}")
                self.use_local_ai = False

        # Online fallback
        try:
            print("🌐 Using online AI...")
            url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
            headers = {}
            payload = {"inputs": query}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            data = res.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"]
            return "I’m having trouble thinking right now."
        except Exception as e:
            print(f"🌐 Online AI failed: {e}")
            return "My AI brain isn’t available."

    # -----------------------------
    # COMMAND HANDLING
    # -----------------------------
    async def handle_command(self, text: str):
        if not text:
            await self.speak("Sorry, I didn't hear you.")
            return

        if "time" in text:
            now = datetime.now().strftime("%I:%M %p")
            await self.speak(f"The time is {now}.")
        elif "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            await self.speak("Opening YouTube.")
        elif "open notepad" in text:
            os.system("notepad.exe")
            await self.speak("Opening Notepad.")
        elif "open google" in text:
            webbrowser.open("https://www.google.com")
            await self.speak("Opening Google.")
        elif "exit" in text or "stop" in text:
            await self.speak("Goodbye!")
            self.running = False
        else:
            reply = self.ask_ai(text)
            await self.speak(reply)

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    async def run(self):
        try:
            while self.running:
                pcm = self.stream.read(
                    self.porcupine.frame_length, exception_on_overflow=False
                )
                pcm_unpacked = struct.unpack_from(
                    "h" * self.porcupine.frame_length, pcm
                )
                keyword_index = self.porcupine.process(pcm_unpacked)

                if keyword_index >= 0:
                    print("🟢 Wake word detected: Jarvis")
                    await self.speak("Yes, I’m listening.")
                    command = self.transcribe()
                    await self.handle_command(command)
                    await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            await self.speak("Shutting down.")
        finally:
            self.cleanup()

    def cleanup(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.porcupine.delete()
        print("🔴 Jarvis stopped.")


# -----------------------------
# ENTRY POINT
# -----------------------------
def main():
    jarvis = JarvisDaemon()
    asyncio.run(jarvis.run())


if __name__ == "__main__":
    main()
