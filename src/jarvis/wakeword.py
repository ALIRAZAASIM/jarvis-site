import pvporcupine
import sounddevice as sd
import struct
import threading

class WakeWordListener:
    def __init__(self, keyword="jarvis", callback=None):
        self.callback = callback
        self._stop = False
        self.keyword = keyword
        self._init_porcupine()

    def _init_porcupine(self):
        self.porcupine = pvporcupine.create(keyword_paths=[pvporcupine.KEYWORDS[self.keyword]])
        self.samplerate = 16000
        self.blocksize = 512

    def start(self):
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        with sd.InputStream(channels=1, samplerate=self.samplerate, blocksize=self.blocksize, dtype="int16") as stream:
            while not self._stop:
                pcm = stream.read(self.blocksize)[0]
                pcm = struct.unpack_from("h" * self.blocksize, pcm)
                result = self.porcupine.process(pcm)
                if result >= 0 and self.callback:
                    self.callback()

    def stop(self):
        self._stop = True
        self.porcupine.delete()
