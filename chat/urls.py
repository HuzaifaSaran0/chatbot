from django.urls import path, include
from .views import ChatAPIView, GroqChatAPIView, GroqChatTwoAPIView, TelegramBotAPIView, GoogleLogin

urlpatterns = [
    path("chat/", ChatAPIView.as_view(), name="chat"),
    path("groq-chat/", GroqChatAPIView.as_view(), name="groq_chat"),  # NEW
    path("groq-chat-two/", GroqChatTwoAPIView.as_view(), name="groq_chat-two"),  # NEW
    path("telegram/", TelegramBotAPIView.as_view(), name="telegram-webhook"),
    path('auth/', include('dj_rest_auth.urls')),  # login/logout
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # signup
    path('auth/google/', GoogleLogin.as_view(), name='google_login')

]
