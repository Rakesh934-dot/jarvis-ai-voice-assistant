
# JARVIS — AI Voice Assistant for macOS

A Python-based voice assistant that combines speech recognition, local large language models, and macOS automation to execute everyday tasks through natural-language commands.

**Status:** Active development | **Platform:** macOS (Apple Silicon)

## Overview

JARVIS is a personal software engineering project focused on building a responsive, locally powered voice assistant. It integrates audio capture, speech transcription, command routing, AI-generated responses, and text-to-speech into one application.

The project emphasizes modular software design, system integration, and practical debugging.

## Features

- Voice interaction with a "Hey Jarvis" wake phrase
- Speech transcription using MLX Whisper
- Local language-model inference using Ollama
- Command routing for supported macOS tasks
- Application launching and music commands
- Conversational memory using SQLite
- Spoken responses through macOS text-to-speech
- Microphone selection by device name for improved reliability

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Speech recognition | MLX Whisper |
| Local AI inference | Ollama |
| Language model | Qwen3:4b |
| Database | SQLite |
| Voice output | macOS text-to-speech |
| Development | VS Code, Git, GitHub |

## System Architecture

```text
       User Voice Input
              |
              v
      Microphone Capture
              |
              v
     MLX Whisper (Speech)
              |
              v
       Text Transcription
              |
              v
        Command Router
          /        \
         v          v
  Fixed Commands   AI Brain
         |          |
         |       Ollama LLM
         |          |
         |     Conversation
         |       Memory
          \        /
           v      v
       Response Output
              |
              v
      macOS Text-to-Speech
```

## Engineering Challenges

### Microphone Reliability

During development, JARVIS occasionally stopped receiving audio when macOS switched between the built-in microphone and connected AirPods.

I investigated the device-selection behavior and changed the implementation to identify the intended microphone by its device name rather than relying on a potentially changing device index.

### Integrating Multiple Components

JARVIS connects audio input, speech recognition, command execution, local AI inference, and voice output.

Separating these responsibilities into Python modules has helped make the application easier to debug and extend.

### Responsiveness

During local testing on Apple Silicon, I measured approximately 1.1 seconds to transcribe a 10-second audio command.

This measurement represents a local transcription test, not an end-to-end response-time benchmark.

## Project Structure

```text
jarvis-ai-voice-assistant/
├── jarvis_loop.py
├── fixed_commands.py
├── ai_brain.py
├── conversation_memory.py
├── requirements.txt
├── src/
├── tests/
└── README.md
```

## Getting Started

This project is designed for macOS with Apple Silicon.

It requires Python, the dependencies listed in `requirements.txt`, and a locally configured Ollama installation.

The project is under active development. Setup and compatibility instructions will be expanded as the implementation is tested.

## Future Improvements

- Expand automated testing
- Improve error handling and recovery
- Add structured logging
- Improve command execution reliability
- Add additional automation capabilities
- Document performance benchmarks

## Author

**Rakesh Reddy Ambati**

[LinkedIn](https://www.linkedin.com/in/rakesh-reddy-ambati-b583a7240/) | [GitHub](https://github.com/Rakesh934-dot)

