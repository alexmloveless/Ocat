"""
Text-to-Speech (TTS) commands for Ocat.

Implements TTS functionality using OpenAI's TTS API to convert text responses
to speech and play them back through the terminal.
"""

import os
import tempfile
import subprocess
import asyncio
from typing import List, Any, Optional
from pathlib import Path

from . import command, BaseCommand, CommandResult
from ..exceptions import ConfigError


class TTSError(Exception):
    """Exception raised for TTS-related errors."""

    pass


@command(
    name="speak",
    description="Convert the last assistant response to speech and play it",
    usage="/speak [voice] [model]",
    aliases=["s"],
)
class SpeakCommand(BaseCommand):
    """Command to convert last response to speech using OpenAI TTS."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the speak command.

        Parameters
        ----------
        args : List[str]
            Command arguments: [voice] [model] (both optional)
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Check if TTS is enabled
            if not context.config.tts.enabled:
                return CommandResult.error("TTS is disabled in configuration")

            # Get the last assistant response
            last_response = self._get_last_assistant_response(context)
            if not last_response:
                return CommandResult.error("No assistant response found to speak")

            # Parse arguments
            voice = args[0] if len(args) > 0 else context.config.tts.voice
            model = args[1] if len(args) > 1 else context.config.tts.model

            # Validate voice and model
            if not self._validate_voice(voice):
                return CommandResult.error(
                    f"Invalid voice '{voice}'. Valid voices: alloy, echo, fable, nova, onyx, shimmer"
                )

            if not self._validate_model(model):
                return CommandResult.error(
                    f"Invalid model '{model}'. Valid models: tts-1, tts-1-hd"
                )

            # Generate and play TTS
            await self._generate_and_play_tts(
                text=last_response, voice=voice, model=model, context=context
            )

            return CommandResult.ok(
                f"Spoke last response using voice '{voice}' and model '{model}'"
            )

        except TTSError as e:
            return CommandResult.error(f"TTS error: {e}")
        except Exception as e:
            return CommandResult.error(f"Unexpected error: {e}")


@command(
    name="speaklike",
    description="Convert the last assistant response to speech with custom instructions",
    usage='/speaklike "instructions" [voice] [model]',
    aliases=["sl"],
)
class SpeakLikeCommand(BaseCommand):
    """Command to convert last response to speech with custom instructions."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the speaklike command.

        Parameters
        ----------
        args : List[str]
            Command arguments: instructions [voice] [model]
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Check if TTS is enabled
            if not context.config.tts.enabled:
                return CommandResult.error("TTS is disabled in configuration")

            # Validate arguments
            if len(args) < 1:
                return CommandResult.error(
                    'Instructions are required. Usage: /speaklike "instructions" [voice] [model]'
                )

            # Get the last assistant response
            last_response = self._get_last_assistant_response(context)
            if not last_response:
                return CommandResult.error("No assistant response found to speak")

            # Parse arguments
            instructions = args[0]
            voice = args[1] if len(args) > 1 else context.config.tts.voice
            model = args[2] if len(args) > 2 else context.config.tts.model

            # Validate voice and model
            if not self._validate_voice(voice):
                return CommandResult.error(
                    f"Invalid voice '{voice}'. Valid voices: alloy, echo, fable, nova, onyx, shimmer"
                )

            if not self._validate_model(model):
                return CommandResult.error(
                    f"Invalid model '{model}'. Valid models: tts-1, tts-1-hd"
                )

            # Combine instructions with the response text
            enhanced_text = f"{instructions}\n\n{last_response}"

            # Generate and play TTS
            await self._generate_and_play_tts(
                text=enhanced_text, voice=voice, model=model, context=context
            )

            return CommandResult.ok(
                f"Spoke last response with instructions using voice '{voice}' and model '{model}'"
            )

        except TTSError as e:
            return CommandResult.error(f"TTS error: {e}")
        except Exception as e:
            return CommandResult.error(f"Unexpected error: {e}")

    def _get_last_assistant_response(self, context: Any) -> Optional[str]:
        """
        Get the last assistant response from the conversation history.

        Parameters
        ----------
        context : Any
            Chat session context

        Returns
        -------
        Optional[str]
            Last assistant response content, or None if not found
        """
        # Search backwards through messages for the last assistant response
        for message in reversed(context.messages):
            if message.role == "assistant":
                return message.content
        return None

    def _validate_voice(self, voice: str) -> bool:
        """Validate if the voice is supported."""
        valid_voices = ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]
        return voice.lower() in valid_voices

    def _validate_model(self, model: str) -> bool:
        """Validate if the model is supported."""
        valid_models = ["tts-1", "tts-1-hd"]
        return model in valid_models

    async def _generate_and_play_tts(
        self, text: str, voice: str, model: str, context: Any
    ) -> None:
        """
        Generate TTS audio and play it.

        Parameters
        ----------
        text : str
            Text to convert to speech
        voice : str
            Voice to use for TTS
        model : str
            Model to use for TTS
        context : Any
            Chat session context

        Raises
        ------
        TTSError
            If TTS generation or playback fails
        """
        try:
            # Import OpenAI client
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise TTSError(
                    "OpenAI library not installed. Install with: pip install openai"
                )

            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise TTSError("OPENAI_API_KEY environment variable not set")

            # Initialize OpenAI client
            client = AsyncOpenAI(api_key=api_key)

            # Clean the text for TTS (remove markdown formatting)
            clean_text = self._clean_text_for_tts(text)
            if len(clean_text.strip()) == 0:
                raise TTSError("No readable text found after cleaning")

            # Show progress
            context.console.print(
                f"🔊 Generating speech using {voice} voice...", style="cyan"
            )

            # Generate TTS audio
            response = await client.audio.speech.create(
                model=model, voice=voice, input=clean_text
            )

            # Determine output file path
            audio_dir = Path(context.config.tts.audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename
            import time

            timestamp = int(time.time())
            output_file = audio_dir / f"ocat_tts_{timestamp}.mp3"

            # Save audio to file
            output_file.write_bytes(response.content)

            context.console.print(f"🎵 Audio saved to: {output_file}", style="green")

            # Play the audio file
            await self._play_audio(output_file, context)

        except Exception as e:
            raise TTSError(f"Failed to generate or play TTS: {e}")

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS by removing markdown formatting and other artifacts.

        Parameters
        ----------
        text : str
            Raw text to clean

        Returns
        -------
        str
            Cleaned text suitable for TTS
        """
        import re

        # Remove markdown code blocks
        text = re.sub(r"```[^`]*```", "[code block]", text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove markdown links but keep the text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # Remove bold/italic markdown
        text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^\*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Remove headers
        text = re.sub(r"^#+\s*(.+)$", r"\1", text, flags=re.MULTILINE)

        # Remove list markers
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Remove extra whitespace and normalize
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    async def _play_audio(self, audio_file: Path, context: Any) -> None:
        """
        Play audio file using system audio player.

        Parameters
        ----------
        audio_file : Path
            Path to the audio file to play
        context : Any
            Chat session context

        Raises
        ------
        TTSError
            If audio playback fails
        """
        try:
            context.console.print(f"🎧 Playing audio...", style="yellow")

            # Determine the appropriate audio player for the system
            if os.name == "nt":  # Windows
                player_cmd = ["start", str(audio_file)]
                use_shell = True
            elif os.uname().sysname == "Darwin":  # macOS
                player_cmd = ["afplay", str(audio_file)]
                use_shell = False
            else:  # Linux and other Unix-like systems
                # Try common Linux audio players
                for player in ["mpg123", "ffplay", "aplay", "paplay"]:
                    if (
                        subprocess.run(
                            ["which", player], capture_output=True
                        ).returncode
                        == 0
                    ):
                        if player == "ffplay":
                            player_cmd = [
                                "ffplay",
                                "-nodisp",
                                "-autoexit",
                                str(audio_file),
                            ]
                        else:
                            player_cmd = [player, str(audio_file)]
                        use_shell = False
                        break
                else:
                    raise TTSError(
                        "No suitable audio player found. Please install mpg123, ffplay, or another audio player."
                    )

            # Play the audio
            process = await asyncio.create_subprocess_exec(
                *player_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                shell=use_shell if os.name == "nt" else False,
            )

            await process.wait()

            if process.returncode != 0:
                raise TTSError(f"Audio player exited with code {process.returncode}")

            context.console.print("✅ Audio playback completed", style="green")

        except Exception as e:
            raise TTSError(f"Failed to play audio: {e}")


# Make the methods available in the base class
SpeakCommand._get_last_assistant_response = (
    SpeakLikeCommand._get_last_assistant_response
)
SpeakCommand._validate_voice = SpeakLikeCommand._validate_voice
SpeakCommand._validate_model = SpeakLikeCommand._validate_model
SpeakCommand._generate_and_play_tts = SpeakLikeCommand._generate_and_play_tts
SpeakCommand._clean_text_for_tts = SpeakLikeCommand._clean_text_for_tts
SpeakCommand._play_audio = SpeakLikeCommand._play_audio
