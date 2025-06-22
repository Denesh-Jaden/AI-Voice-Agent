# # Install the assemblyai package by executing the command "pip install assemblyai"

import assemblyai as aai
from dotenv import load_dotenv
import os

# aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# # audio_file = "./local_file.mp3"
# audio_file = "https://assembly.ai/wildfires.mp3"

# config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)

# transcript = aai.Transcriber(config=config).transcribe(audio_file)

# if transcript.status == "error":
#   raise RuntimeError(f"Transcription failed: {transcript.error}")

# print(transcript.text)


# Install the assemblyai package by executing the command "pip install assemblyai"

import logging
from typing import Type

import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not api_key: 
    raise ValueError("Please set the ASSEMBLYAI_API_KEY environment variable.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")


def on_turn(self: Type[StreamingClient], event: TurnEvent):
    print(f"{event.transcript} ({event.end_of_turn})")

    if event.end_of_turn and not event.turn_is_formatted:
        params = StreamingSessionParameters(
            format_turns=True,
        )

        self.set_params(params)


def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    print(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )


def on_error(self: Type[StreamingClient], error: StreamingError):
    print(f"Error occurred: {error}")


def main():
    client = StreamingClient(
        StreamingClientOptions(
            api_key=api_key,
            api_host="streaming.assemblyai.com",
        )
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    client.connect(
        StreamingParameters(
            sample_rate=16000,
            format_turns=True,
        )
    )

    try:
        client.stream(
          aai.extras.MicrophoneStream(sample_rate=16000)
        )
    finally:
        client.disconnect(terminate=True)


if __name__ == "__main__":
    main()
