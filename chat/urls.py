from django.urls import path
from .views import ChatAPIView, GroqChatAPIView, GroqChatTwoAPIView, TelegramBotAPIView

urlpatterns = [
    path("chat/", ChatAPIView.as_view(), name="chat"),
    path("groq-chat/", GroqChatAPIView.as_view(), name="groq_chat"),  # NEW
    path("groq-chat-two/", GroqChatTwoAPIView.as_view(), name="groq_chat-two"),  # NEW
    path("telegram/", TelegramBotAPIView.as_view(), name="telegram-webhook"),
]
