from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Hero, Team, Player, Tournament, Match, Game, GameDraft, GameLineup, SideChoice, DraftChoice, LaneChoice

class ESportsAPITests(APITestCase):
    def setUp(self):
        # Create core entities
        self.hero1 = Hero.objects.create(name_ppl="Florentino", name_en="Florentino", name_vn="Florentino")
        self.hero2 = Hero.objects.create(name_ppl="Tulen", name_en="Tulen", name_vn="Tulen")
        
        self.team1 = Team.objects.create(name="Agfox", region="CN")
        self.team2 = Team.objects.create(name="Nova eSports", region="CN")
        
        self.player1 = Player.objects.create(ign="Fly", name="Fly", team=self.team1, default_role="CLASH")
        self.player2 = Player.objects.create(ign="Tiger", name="Tiger", team=self.team2, default_role="MID")
        
        self.tournament = Tournament.objects.create(name="AIC 2026", game_version="HOK", year=2026)
        
        # Create match and game structure
        self.match = Match.objects.create(
            tournament=self.tournament,
            home_team_ref=self.team1,
            away_team_ref=self.team2,
            home_team_score=2,
            away_team_score=0,
            stage="Grand Finals",
            date="2026-06-13"
        )
        
        self.game = Game.objects.create(
            match=self.match,
            game_number=1,
            duration="18:42",
            blue_side_team=self.team1,
            red_side_team=self.team2,
            winner_side=SideChoice.BLUE
        )
        
        # Create drafts
        self.draft1 = GameDraft.objects.create(
            game=self.game,
            slot=1,
            hero=self.hero1,
            team=self.team1,
            action_type=DraftChoice.BAN
        )
        
        # Create lineups
        self.lineup1 = GameLineup.objects.create(
            game=self.game,
            player=self.player1,
            hero=self.hero2,
            lane=LaneChoice.CLASH,
            kills=5,
            deaths=2,
            assists=8,
            gold=12000,
            is_mvp=True
        )

    def test_list_endpoints(self):
        endpoints = ['hero', 'team', 'player', 'tournament', 'match', 'game', 'draft', 'lineup']
        for ep in endpoints:
            url = reverse(f'{ep}-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Endpoint {ep}-list failed")

    def test_game_nested_detail(self):
        url = reverse('game-detail', kwargs={'pk': self.game.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify nested JSON structure
        data = response.json()
        self.assertIn('drafts', data)
        self.assertIn('blue_lineup', data)
        self.assertIn('red_lineup', data)
        self.assertEqual(len(data['drafts']), 1)
        self.assertEqual(len(data['blue_lineup']), 1)
        self.assertEqual(len(data['red_lineup']), 0)
        
        draft = data['drafts'][0]
        self.assertEqual(draft['hero_name'], "Florentino")
        self.assertEqual(draft['team_name'], "Agfox")
        self.assertEqual(draft['action_type'], "BAN")
        
        lineup = data['blue_lineup'][0]
        self.assertEqual(lineup['player_ign'], "Fly")
        self.assertEqual(lineup['hero_name'], "Tulen")
        self.assertEqual(lineup['lane'], "CLASH")
        self.assertEqual(lineup['kills'], 5)
        self.assertTrue(lineup['is_mvp'])

    def test_match_nested_detail(self):
        url = reverse('match-detail', kwargs={'pk': self.match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('games', data)
        self.assertEqual(len(data['games']), 1)
        
        game = data['games'][0]
        self.assertIn('drafts', game)
        self.assertIn('blue_lineup', game)
        self.assertIn('red_lineup', game)
