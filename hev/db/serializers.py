from rest_framework import serializers
from .models import Hero, Team, Player, Tournament, Match, Game, GameDraft, GameLineup

class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hero
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class PlayerSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    signature_hero_name = serializers.CharField(source='signature_hero.name_ppl', read_only=True)

    class Meta:
        model = Player
        fields = ['id', 'name', 'ign', 'team', 'team_name', 'default_role', 'signature_hero', 'signature_hero_name']


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = '__all__'


class GameDraftSerializer(serializers.ModelSerializer):
    hero_name = serializers.CharField(source='hero.name_ppl', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = GameDraft
        fields = ['id', 'game', 'slot', 'hero', 'hero_name', 'team', 'team_name', 'action_type']


class GameLineupSerializer(serializers.ModelSerializer):
    player_ign = serializers.CharField(source='player.ign', read_only=True)
    hero_name = serializers.CharField(source='hero.name_ppl', read_only=True)

    class Meta:
        model = GameLineup
        fields = ['id', 'game', 'player', 'player_ign', 'hero', 'hero_name', 'lane', 'kills', 'deaths', 'assists']


class GameSerializer(serializers.ModelSerializer):
    blue_side_team_name = serializers.CharField(source='blue_side_team.name', read_only=True)
    red_side_team_name = serializers.CharField(source='red_side_team.name', read_only=True)
    mvp_player_ign = serializers.CharField(source='mvp_player.ign', read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'match', 'game_number', 'duration', 'blue_side_team', 'blue_side_team_name', 'red_side_team', 'red_side_team_name', 'winner_side', 'mvp_player', 'mvp_player_ign']


class GameDetailSerializer(serializers.ModelSerializer):
    blue_side_team_name = serializers.CharField(source='blue_side_team.name', read_only=True)
    red_side_team_name = serializers.CharField(source='red_side_team.name', read_only=True)
    mvp_player_ign = serializers.CharField(source='mvp_player.ign', read_only=True)
    drafts = GameDraftSerializer(many=True, read_only=True)
    blue_lineup = serializers.SerializerMethodField()
    red_lineup = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'match', 'game_number', 'duration', 
            'blue_side_team', 'blue_side_team_name', 
            'red_side_team', 'red_side_team_name', 
            'winner_side', 'mvp_player', 'mvp_player_ign', 
            'drafts', 'blue_lineup', 'red_lineup'
        ]

    def _get_sorted_lineup_for_team(self, game_obj, team_obj):
        lane_order = {
            'CLASH': 1,
            'JUNGLE': 2,
            'MID': 3,
            'FARM': 4,
            'ROAM': 5
        }
        # Filter lineups belonging to this team's players
        lineups = game_obj.lineups.filter(player__team=team_obj).select_related('player', 'hero')
        sorted_lineups = sorted(lineups, key=lambda l: lane_order.get(l.lane, 99))
        return GameLineupSerializer(sorted_lineups, many=True).data

    def get_blue_lineup(self, obj):
        return self._get_sorted_lineup_for_team(obj, obj.blue_side_team)

    def get_red_lineup(self, obj):
        return self._get_sorted_lineup_for_team(obj, obj.red_side_team)


class MatchSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team_ref.name', read_only=True)
    away_team_name = serializers.CharField(source='away_team_ref.name', read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'tournament', 'tournament_name', 'home_team_ref', 'home_team_name', 'away_team_ref', 'away_team_name', 'home_team_score', 'away_team_score', 'stage', 'date']


class MatchDetailSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team_ref.name', read_only=True)
    away_team_name = serializers.CharField(source='away_team_ref.name', read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    games = GameDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'tournament', 'tournament_name', 'home_team_ref', 'home_team_name', 'away_team_ref', 'away_team_name', 'home_team_score', 'away_team_score', 'stage', 'date', 'games']
