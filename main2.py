# import assemblyai as aai
# from elevenlabs.client import ElevenLabs
# from elevenlabs import stream
# import ollama
# from dotenv import load_dotenv
# import os
# import logging
# import sys

# load_dotenv()

# # Set up logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#         logging.FileHandler(os.path.join(os.path.dirname(__file__), 'app.log'))
#     ]
# )
# logger = logging.getLogger('AI-Voice-Agent')

# logger.info("Starting main2.py")


# class AIVoiceAgent:
#     def __init__(self):
#         aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
#         self.client = ElevenLabs(
#             api_key = os.getenv("ELEVENLABS_API_KEY"),
#         )

#         self.transcriber = None

#         self.full_transcript = [
#             {"role":"system", "content":"You are a language model called R1 created by DeepSeek, answer the questions being asked in less than 300 characters."},
#         ]

#     def start_transcription(self):
#         print(f"\nReal-time transcription: ", end="\r\n")
#         self.transcriber = aai.RealtimeTranscriber(
#           sample_rate=16_000,
#           on_data=self.on_data,
#           on_error=self.on_error,
#           on_open=self.on_open,
#           on_close=self.on_close,
#       )
#         self.transcriber.connect()
#         microphone_stream = aai.extras.MicrophoneStream(sample_rate=16_000)
#         logger.debug("Initializing microphone")
#         self.transcriber.stream(microphone_stream)
#         logger.debug("Microphone initialized")

#     def stop_transcription(self):
#       if self.transcriber:
#           self.transcriber.close()
#           self.transcriber = None

#     def on_open(self, session_opened: aai.RealtimeSessionOpened):
#         #print("Session ID:", session_opened.session_id)
#         return
    
#     def on_data(self, transcript: aai.RealtimeTranscript):
#         if not transcript.text:
#             return

#         if isinstance(transcript, aai.RealtimeFinalTranscript):
#             print(transcript.text)
#             self.generate_ai_response(transcript)
#         else:
#             print(transcript.text, end="\r")

#     def on_error(self, error: aai.RealtimeError):
#         #print("An error occured:", error)
#         return

#     def on_close(self):
#         #print("Closing Session")
#         return    
    
#     def generate_ai_response(self, transcript):
#         self.stop_transcription()

#         self.full_transcript.append({"role":"user", "content":transcript.text})
#         print(f"\nUser:{transcript.text}", end="\r\n")

#         ollama_stream = ollama.chat(
#             model = "deepseek-r1:7b",
#             messages = self.full_transcript,
#             stream = True,
#         )

#         print("DeepSeek R1:", end="\r\n")
#         text_buffer = ""
#         full_text = ""
#         for chunk in ollama_stream:
#             text_buffer += chunk['message']['content']
#             logger.debug("Processing audio frame")
#             if text_buffer.endswith('.'):
#                 audio_stream = self.client.generate(text=text_buffer,
#                                                     model="eleven_turbo_v2",
#                                                     stream=True)
#                 print(text_buffer, end="\n", flush=True)
#                 stream(audio_stream)
#                 full_text += text_buffer
#                 text_buffer = ""

#         if text_buffer:
#             audio_stream = self.client.generate(text=text_buffer,
#                                                     model="eleven_turbo_v2",
#                                                     stream=True)
#             print(text_buffer, end="\n", flush=True)
#             stream(audio_stream)
#             full_text += text_buffer

#         self.full_transcript.append({"role":"assistant", "content":full_text})

#         self.start_transcription()

# ai_voice_agent = AIVoiceAgent()
# ai_voice_agent.start_transcription()


import os
import tempfile
from typing import Type, IO
from io import BytesIO
import pygame
from pygame import mixer
import time

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
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import ollama
from dotenv import load_dotenv

# Initialize pygame mixer at the beginning
pygame.init()
mixer.init()

load_dotenv()

api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not api_key:
    raise ValueError("Please set the ASSEMBLYAI_API_KEY environment variable.")

class AIVoiceAgent:
    def __init__(self):
        self.client = ElevenLabs(
            api_key = os.getenv("ELEVENLABS_API_KEY"),
        )
        self.full_transcript = [
            {"role":"system", "content":"You are a language model called R1 created by DeepSeek, answer the questions being asked in less than 300 characters."},
        ]
        self.streaming_client = None
        # Create a temp directory for audio files
        self.temp_dir = tempfile.mkdtemp()
        print(f"Using temporary directory for audio: {self.temp_dir}")

    def text_to_speech_stream(self, text: str) -> IO[bytes]:
        # Perform the text-to-speech conversion
        response = self.client.text_to_speech.stream(
            voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_multilingual_v2",
            # Optional voice settings that allow you to customize the output
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        )

        # Create a BytesIO object to hold the audio data in memory
        audio_stream = BytesIO()

        # Write each chunk of audio data to the stream
        for chunk in response:
            if chunk:
                audio_stream.write(chunk)

        # Reset stream position to the beginning
        audio_stream.seek(0)

        # Return the stream for further use
        return audio_stream
    
    def play_audio(self, audio_stream):
        try:
            # Create a unique temporary file path in our temp directory
            temp_file = os.path.join(self.temp_dir, f"audio_{time.time()}.mp3")
            
            # Save the BytesIO stream to a temporary file
            with open(temp_file, "wb") as f:
                f.write(audio_stream.read())
            
            # Reset the BytesIO stream position
            audio_stream.seek(0)
            
            print(f"Playing audio from {temp_file}")
            
            # Load and play the audio file
            mixer.music.load(temp_file)
            mixer.music.play()
            
            # Wait for the audio to finish playing
            while mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Clean up the temporary file
            os.remove(temp_file)
        except Exception as e:
            print(f"Error playing audio: {str(e)}")

    def on_begin(self, client: Type[StreamingClient], event: BeginEvent):
        print(f"Session started: {event.id}")

    def on_turn(self, client: Type[StreamingClient], event: TurnEvent):
        transcript_text = event.transcript
        print(f"{transcript_text} ({event.end_of_turn})")

        if event.end_of_turn and not event.turn_is_formatted:
            params = StreamingSessionParameters(
                format_turns=True,
            )
            client.set_params(params)

        if event.end_of_turn:
            self.generate_ai_response(transcript_text)

    def on_terminated(self, client: Type[StreamingClient], event: TerminationEvent):
        duration = event.audio_duration_seconds
        print(f"Session terminated: {duration} seconds of audio processed")

    def on_error(self, client: Type[StreamingClient], error: StreamingError):
        print(f"Error occurred: {error}")

    def start_transcription(self):
        self.streaming_client = StreamingClient(
            StreamingClientOptions(
                api_key=api_key,
                api_host="streaming.assemblyai.com",
            )
        )

        self.streaming_client.on(StreamingEvents.Begin, self.on_begin)
        self.streaming_client.on(StreamingEvents.Turn, self.on_turn)
        self.streaming_client.on(StreamingEvents.Termination, self.on_terminated)
        self.streaming_client.on(StreamingEvents.Error, self.on_error)

        self.streaming_client.connect(
            StreamingParameters(
                sample_rate=16000,
                format_turns=True,
            )
        )

        mic_stream = aai.extras.MicrophoneStream(sample_rate=16000)

        print("Real-time transcription:")
        print("Speak into your microphone...")

        try:
            self.streaming_client.stream(mic_stream)
        except Exception as e:
            print(f"Error during streaming: {str(e)}")
        finally:
            if self.streaming_client is not None:
                self.streaming_client.disconnect(terminate=True)
                self.streaming_client = None

    def generate_ai_response(self, transcript_text):
        if self.streaming_client is not None:
            self.streaming_client.disconnect(terminate=True)
            self.streaming_client = None

        self.full_transcript.append({"role":"user", "content":transcript_text})
        print(f"\nUser:{transcript_text}", end="\r\n")

        ollama_stream = ollama.chat(
            model = "deepseek-r1:7b",
            messages = self.full_transcript,
            stream = True,
        )

        print("DeepSeek R1:", end="\r\n")
        text_buffer = ""
        full_text = ""
        for chunk in ollama_stream:
            text_buffer += chunk['message']['content']
            if text_buffer.endswith('.'):
                # Using the new text_to_speech_stream method
                audio_stream = self.text_to_speech_stream(text_buffer)
                print(text_buffer, end="\n", flush=True)
                # Use pygame instead of stream()
                self.play_audio(audio_stream)
                full_text += text_buffer
                text_buffer = ""

        if text_buffer:
            # Using the new text_to_speech_stream method
            audio_stream = self.text_to_speech_stream(text_buffer)
            print(text_buffer, end="\n", flush=True)
            # Use pygame instead of stream()
            self.play_audio(audio_stream)
            full_text += text_buffer

        self.full_transcript.append({"role":"assistant", "content":full_text})
        self.start_transcription()

if __name__ == "__main__":
    ai_voice_agent = AIVoiceAgent()
    ai_voice_agent.start_transcription()