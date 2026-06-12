"""
URL configuration for hev project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from db.views import (
    HeroViewSet, TeamViewSet, PlayerViewSet, TournamentViewSet,
    MatchViewSet, GameViewSet, GameDraftViewSet, GameLineupViewSet
)

router = DefaultRouter()
router.register(r'heroes', HeroViewSet, basename='hero')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'tournaments', TournamentViewSet, basename='tournament')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'games', GameViewSet, basename='game')
router.register(r'drafts', GameDraftViewSet, basename='draft')
router.register(r'lineups', GameLineupViewSet, basename='lineup')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # API Schema & Documentation Endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]


