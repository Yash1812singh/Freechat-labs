from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings

class ChatbotAPIView(APIView):
    def post(self, request):
        user_message = request.data.get("message")

        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }

        try:
            response = requests.post(settings.GROQ_API_URL, headers=headers, json=data)
            #print("🔍 Groq raw response:", response.text)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Request failed: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response_data = response.json()
            print("🔍 Groq raw response:", response.text)
            ai_reply = response_data["choices"][0]["message"]["content"]
            return Response({"reply": ai_reply})
        except Exception as e:
            return Response({"error": "Failed to parse Groq response", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
