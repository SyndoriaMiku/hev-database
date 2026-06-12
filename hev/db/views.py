from rest_framework import viewsets
from .models import Hero, Team, Player, Tournament, Match, Game, GameDraft, GameLineup
from .serializers import (
    HeroSerializer, TeamSerializer, PlayerSerializer, TournamentSerializer,
    MatchSerializer, MatchDetailSerializer, GameSerializer, GameDetailSerializer,
    GameDraftSerializer, GameLineupSerializer
)

class HeroViewSet(viewsets.ModelViewSet):
    queryset = Hero.objects.all()
    serializer_class = HeroSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all().select_related('team', 'signature_hero')
    serializer_class = PlayerSerializer


class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all().select_related('tournament', 'home_team_ref', 'away_team_ref')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MatchDetailSerializer
        return MatchSerializer


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all().select_related('match', 'blue_side_team', 'red_side_team', 'mvp_player')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GameDetailSerializer
        return GameSerializer


class GameDraftViewSet(viewsets.ModelViewSet):
    queryset = GameDraft.objects.all().select_related('game', 'hero', 'team')
    serializer_class = GameDraftSerializer


class GameLineupViewSet(viewsets.ModelViewSet):
    queryset = GameLineup.objects.all().select_related('game', 'player', 'hero')
    serializer_class = GameLineupSerializer
