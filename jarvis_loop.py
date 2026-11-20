
import subprocess
import threading
import time
import sys
from collections import deque

import mlx_whisper
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

from fixed_commands import handle_command
from ai_brain import ask_jarvis


# ==========================================
# JARVIS - PHASE 10
# CONTINUOUS CONVERSATION + INTERRUPTIBLE VOICE
# ==========================================

SAMPLE_RATE = 16000
CHUNK = 1280

WHISPER_MODEL = "mlx-community/whisper-small-mlx"

# Recording configuration
MAX_RECORD_SECONDS = 20
WAIT_FOR_SPEECH_SECONDS = 8
SILENCE_SECONDS = 1.5
MIN_SPEECH_SECONDS = 0.3
PRE_ROLL_SECONDS = 0.4

# Keep your working microphone sensitivity
MIN_VOICE_RMS = 0.006
NOISE_MULTIPLIER = 2.0

# Conversation configuration
CONVERSATION_TIMEOUT = 60

# Voice configuration
VOICE_NAME = "Samantha"
VOICE_RATE = 195

# Speech process management
speech_process = None
speech_lock = threading.Lock()
speech_generation = 0

END_CONVERSATION_COMMANDS = {
    "end conversation",
    "end the conversation",
    "exit conversation",
    "stop conversation",
    "go to sleep",
    "jarvis go to sleep",
    "that's all jarvis",
    "that is all jarvis",
}

SHUTDOWN_COMMANDS = {
    "stop jarvis",
    "exit jarvis",
    "goodbye jarvis",
    "shut down jarvis",
    "shutdown jarvis",
}


# ==========================================
# MICROPHONE
# ==========================================

def find_macbook_mic():
    for i, device in enumerate(sd.query_devices()):
        if (
            "MacBook Air Microphone" in device["name"]
            and device["max_input_channels"] > 0
        ):
            return i

    return None


MIC = find_macbook_mic()


# ==========================================
# INTERRUPTIBLE SPEECH OUTPUT
# ==========================================

def speak(text):
    global speech_process
    global speech_generation

    text = str(text).strip()

    if not text:
        return

    print(f"Jarvis: {text}", flush=True)

    start = time.perf_counter()

    with speech_lock:
        speech_generation += 1
        generation = speech_generation

        # Stop any previous JARVIS speech.
        previous = speech_process

        if previous is not None and previous.poll() is None:
            previous.terminate()

        process = subprocess.Popen(
            [
                "say",
                "-v", VOICE_NAME,
                "-r", str(VOICE_RATE),
                text
            ]
        )

        speech_process = process

    try:
        process.wait()

    finally:
        elapsed = time.perf_counter() - start

        with speech_lock:
            if (
                speech_generation == generation
                and speech_process is process
            ):
                speech_process = None

        print(
            f"[JARVIS] Speech time: {elapsed:.2f}s",
            flush=True
        )


def stop_speaking():
    global speech_process
    global speech_generation

    with speech_lock:
        process = speech_process

        if process is None or process.poll() is not None:
            return False

        speech_generation += 1
        speech_process = None

        process.terminate()

    try:
        process.wait(timeout=2)

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    print(
        "[JARVIS] Speech interrupted.",
        flush=True
    )

    return True


def is_speaking():
    with speech_lock:
        return (
            speech_process is not None
            and speech_process.poll() is None
        )


def beep():
    subprocess.run(
        [
            "afplay",
            "/System/Library/Sounds/Ping.aiff"
        ],
        check=False
    )


# ==========================================
# WAKE WORD
# ==========================================

def wait_for_wake(model):
    print(
        "\nListening for 'Hey Jarvis'..."
        " (Ctrl+C to stop)",
        flush=True
    )

    model.reset()

    with sd.InputStream(
        device=MIC,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK
    ) as stream:

        while True:
            audio, overflowed = stream.read(CHUNK)

            if overflowed:
                print(
                    "[JARVIS WARNING] Wake audio overflow."
                )

            prediction = model.predict(
                audio.flatten()
            )

            score = prediction.get(
                "hey_jarvis", 0
            )

            if score > 0.5:
                model.reset()

                print(
                    "Jarvis: Wake word detected.",
                    flush=True
                )

                return


# ==========================================
# VOICE ACTIVITY DETECTION
# ==========================================

def audio_rms(audio):
    samples = audio.astype(np.float32)

    return float(
        np.sqrt(np.mean(samples * samples))
    )


def record_command(
    wait_seconds=WAIT_FOR_SPEECH_SECONDS
):
    print(
        "Jarvis: I'm listening. Speak naturally...",
        flush=True
    )

    chunk_seconds = CHUNK / SAMPLE_RATE

    pre_roll_chunks = max(
        1,
        int(PRE_ROLL_SECONDS / chunk_seconds)
    )

    pre_roll = deque(
        maxlen=pre_roll_chunks
    )

    recorded_chunks = []

    speech_started = False
    speech_time = 0.0
    silence_time = 0.0
    waiting_time = 0.0
    total_time = 0.0

    noise_floor = 0.003

    with sd.InputStream(
        device=MIC,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK
    ) as stream:

        while total_time < MAX_RECORD_SECONDS:
            audio, overflowed = stream.read(CHUNK)

            if overflowed:
                print(
                    "[JARVIS WARNING] Microphone overflow."
                )

            chunk = audio.flatten().copy()
            level = audio_rms(chunk)

            total_time += chunk_seconds

            threshold = max(
                MIN_VOICE_RMS,
                noise_floor * NOISE_MULTIPLIER
            )

            is_voice = level >= threshold

            if not speech_started:
                pre_roll.append(chunk)

                if is_voice:
                    speech_started = True

                    recorded_chunks.extend(
                        pre_roll
                    )

                    pre_roll.clear()

                    speech_time += chunk_seconds

                    print(
                        "Jarvis: Speech detected.",
                        flush=True
                    )

                else:
                    waiting_time += chunk_seconds

                    noise_floor = (
                        0.95 * noise_floor
                        + 0.05 * level
                    )

                    if waiting_time >= wait_seconds:
                        print(
                            "Jarvis: No speech detected.",
                            flush=True
                        )

                        return np.array(
                            [],
                            dtype=np.float32
                        )

            else:
                recorded_chunks.append(chunk)

                if is_voice:
                    speech_time += chunk_seconds
                    silence_time = 0.0

                else:
                    silence_time += chunk_seconds

                if (
                    speech_time >= MIN_SPEECH_SECONDS
                    and silence_time >= SILENCE_SECONDS
                ):
                    print(
                        "Jarvis: End of speech detected.",
                        flush=True
                    )

                    break

    if not speech_started or not recorded_chunks:
        return np.array(
            [],
            dtype=np.float32
        )

    audio = np.concatenate(
        recorded_chunks
    )

    print(
        f"Jarvis: Recorded "
        f"{len(audio) / SAMPLE_RATE:.1f} seconds.",
        flush=True
    )

    return audio


# ==========================================
# WHISPER TRANSCRIPTION
# ==========================================

def transcribe(audio):
    if audio.size == 0:
        return ""

    print(
        "Jarvis: Transcribing your speech...",
        flush=True
    )

    start = time.perf_counter()

    result = mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=WHISPER_MODEL,
        language="en"
    )

    elapsed = time.perf_counter() - start

    print(
        f"[JARVIS] Transcription time: "
        f"{elapsed:.2f}s",
        flush=True
    )

    return result["text"].strip()


# ==========================================
# COMMAND PROCESSING
# ==========================================

def normalize_command(command):
    return " ".join(
        command.lower().strip(" .!?").split()
    )


def process_command(command):
    command = command.strip()

    if not command:
        return (
            "Sorry Rakesh, I did not catch that."
        )

    try:
        fixed_answer = handle_command(command)

        if fixed_answer is not None:
            return str(fixed_answer)

        print(
            "Jarvis: Asking AI brain...",
            flush=True
        )

        return ask_jarvis(command)

    except Exception as error:
        print(
            f"[JARVIS ERROR] {error}"
        )

        return (
            "Rakesh, I encountered an error "
            "processing your request."
        )


# ==========================================
# CONTINUOUS CONVERSATION
# ==========================================

def conversation_mode():
    print(
        "\n[JARVIS] Conversation mode activated.",
        flush=True
    )

    print(
        "[JARVIS] You can now speak "
        "without saying Hey Jarvis.",
        flush=True
    )

    last_activity = time.monotonic()

    while True:
        remaining = (
            CONVERSATION_TIMEOUT
            - (time.monotonic() - last_activity)
        )

        if remaining <= 0:
            speak(
                "Conversation timed out. "
                "I'll be here when you need me."
            )

            return "sleep"

        wait_seconds = min(
            WAIT_FOR_SPEECH_SECONDS,
            remaining
        )

        audio = record_command(
            wait_seconds=wait_seconds
        )

        if audio.size == 0:
            continue

        command = transcribe(audio)

        print(
            f"You said: {command}",
            flush=True
        )

        if not command:
            continue

        normalized = normalize_command(
            command
        )

        if normalized in SHUTDOWN_COMMANDS:
            speak("Goodbye Rakesh.")
            return "shutdown"

        if normalized in END_CONVERSATION_COMMANDS:
            speak(
                "Of course, Rakesh. "
                "I'll return to standby mode."
            )

            return "sleep"

        last_activity = time.monotonic()

        start = time.perf_counter()

        answer = process_command(command)

        elapsed = time.perf_counter() - start

        print(
            f"Processing time: "
            f"{elapsed:.1f} seconds",
            flush=True
        )

        speak(answer)

        last_activity = time.monotonic()


# ==========================================
# PHASE 10 SPEECH INTERRUPTION TEST
# ==========================================

def test_interruption():
    print(
        "\n[JARVIS TEST] Testing interruptible voice...",
        flush=True
    )

    test_text = (
        "Hello Rakesh. This is Jarvis. "
        "I am testing my new interruptible "
        "speech system. I will begin speaking "
        "and then automatically stop after "
        "two seconds. This is the first step "
        "toward real time voice conversations."
    )

    speaker = threading.Thread(
        target=speak,
        args=(test_text,)
    )

    speaker.start()

    time.sleep(2)

    stopped = stop_speaking()

    speaker.join()

    if stopped:
        print(
            "[TEST PASSED] JARVIS speech "
            "was interrupted successfully.",
            flush=True
        )
    else:
        print(
            "[TEST] Speech had already finished.",
            flush=True
        )


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():
    if MIC is None:
        print(
            "MacBook Air microphone not found."
        )
        return

    print("=" * 48)
    print("JARVIS - PHASE 10")
    print("Continuous Conversation")
    print("Interruptible Speech Engine")
    print("AI Model: Llama 3.2:3b")
    print("Speech Recognition: Whisper")
    print("Memory: SQLite")
    print("Conversation Timeout: 60 seconds")
    print("=" * 48)

    print(
        f"Using microphone: "
        f"{sd.query_devices(MIC)['name']}"
    )

    print(
        "Loading Hey Jarvis wake-word model..."
    )

    wake_model = Model(
        wakeword_models=["hey_jarvis"],
        inference_framework="onnx"
    )

    speak(
        "Hello Rakesh. Jarvis is online "
        "and ready for your commands."
    )

    try:
        while True:
            wait_for_wake(wake_model)

            beep()

            speak(
                "I'm listening, Rakesh."
            )

            result = conversation_mode()

            if result == "shutdown":
                break

            print(
                "\n[JARVIS] Returning to "
                "wake-word standby mode.",
                flush=True
            )

    except KeyboardInterrupt:
        stop_speaking()

        print(
            "\nJarvis stopped. Bye!"
        )

    except Exception as error:
        stop_speaking()

        print(
            f"[JARVIS FATAL ERROR] {error}"
        )


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    if "--test-interrupt" in sys.argv:
        test_interruption()
    else:
        main()
