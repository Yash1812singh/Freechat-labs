import requests
from django.conf import settings

def generate_reply(msg: str) -> str:
    """
    Sends user question to Groq AI and returns answer in interviewee style.
    """

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    interviewee_prompt = """
    You are an interview candidate named Yash Singh responding to questions from an interviewer.
    Follow these rules:

    - Answer professionally and confidently.
    - Use clear, structured responses (bullet points or short paragraphs).
    - Whenever possible, use the STAR method:
        • Situation  
        • Task  
        • Action  
        • Result
    - Highlight your skills, experience, and problem-solving ability.
    - Do NOT sound like an AI.
    - Avoid generic filler like “As an AI model…”.
    - Keep answers concise but strong.
    - Use real-world style explanations, not overly technical unless asked.
    """

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": interviewee_prompt},
            {"role": "user", "content": msg},
        ],
        "temperature": 0.5,
        "max_tokens": 512,
    }

    try:
        response = requests.post(settings.GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        ai_reply = response_data["choices"][0]["message"]["content"]
        return ai_reply.strip()

    except requests.exceptions.RequestException as e:
        return f"⚠️ API request failed: {e}"
    except Exception as e:
        return f"⚠️ Failed to parse Groq response: {e}"
