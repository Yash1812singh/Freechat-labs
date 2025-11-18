from django.urls import path
from .views import ChatbotAPIView
from .views import TranscribeAPIView,GoogleTranscribeAPIView
urlpatterns = [
    path('chat/', ChatbotAPIView.as_view(), name='chatbot'),
    path('transcribe/', TranscribeAPIView.as_view(), name='transcribe'),
    path('google-transcribe/', GoogleTranscribeAPIView.as_view(), name='google-transcribe'),
]
