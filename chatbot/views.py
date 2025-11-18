import os
import tempfile
import subprocess
import requests
import speech_recognition as sr

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from chatbot.utils import generate_reply


# ✅ Load API Key dynamically every request (fixes stale import issue)
def get_groq_key():
    return os.getenv("GROQ_API_KEY")


# ===========================================================
# 🔊 1) GROQ TRANSCRIPTION API
# ===========================================================
class TranscribeAPIView(APIView):
    def post(self, request):
        file_obj = request.FILES.get("file")

        if not file_obj or file_obj.size == 0:
            return Response({"error": "No audio file provided"}, status=400)

        try:
            # Save uploaded snippet to temporary file
            fd, temp_path = tempfile.mkstemp(suffix=".webm")
            os.close(fd)

            with open(temp_path, "wb") as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)

            # 🔑 Load API key properly
            api_key = get_groq_key()
            if not api_key:
                return Response({"error": "GROQ_API_KEY not found"}, status=500)

            # Call GROQ Whisper API
            with open(temp_path, "rb") as audio_file:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": ("audio.webm", audio_file, "audio/webm")},
                    data={"model": "whisper-large-v3-turbo"},
                )

            if response.status_code != 200:
                print("❌ Groq Error:", response.text)
                return Response({
                    "error": "Groq API failed",
                    "details": response.text
                }, status=response.status_code)

            text = response.json().get("text", "").strip()

            return Response({"transcription": text})

        except Exception as e:
            print("❌ Exception:", e)
            return Response({"error": str(e)}, status=500)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# ===========================================================
# 🤖 2) CHATBOT API
# ===========================================================
class ChatbotAPIView(APIView):
    def post(self, request):
        msg = request.data.get("message")

        if not msg:
            return Response({"error": "Message is required"}, status=400)

        reply = generate_reply(msg)
        return Response({"reply": reply})


# ===========================================================
# 🎤 3) GOOGLE SPEECH TRANSCRIPTION API
# ===========================================================
class GoogleTranscribeAPIView(APIView):
    def post(self, request):
        file_obj = request.FILES.get("file")

        if not file_obj or file_obj.size == 0:
            return Response({"error": "No audio file received"}, status=400)

        try:
            # Save input WebM file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_input:
                for chunk in file_obj.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name

            # Skip empty/silent small chunks
            if os.path.getsize(temp_input_path) < 5000:
                return Response({"error": "Audio too short"}, status=400)

            # Convert to WAV using FFmpeg
            temp_output_fd, temp_output_path = tempfile.mkstemp(suffix=".wav")
            os.close(temp_output_fd)

            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_input_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                temp_output_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(result.stderr)

            # Run Google Speech Recognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_output_path) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio)

            return Response({"transcription": text}, status=200)

        except sr.UnknownValueError:
            return Response({"error": "Google could not understand audio"}, status=400)

        except Exception as e:
            print("❌ Google Transcribe ERROR:", e)
            return Response({"error": str(e)}, status=500)

        finally:
            for path in [locals().get("temp_input_path"), locals().get("temp_output_path")]:
                if path and os.path.exists(path):
                    os.remove(path)
