from django.db import models

# Create your models here.

# Choice field

class GameVersionChoice(models.TextChoices):
    VGVD = 'VGVD', 'Chinese Mainland Version'
    HOK = 'HOK', 'Global Version'
    AOV = 'AOV', 'Arna of Valor Version'
    
class LaneChoice(models.TextChoices):
    CLASH = 'CLASH', 'Clash lane'
    JUNGLE = 'JUNGLE', 'Jungle'
    MID = 'MID', 'Mid lane'
    FARM = 'FARM', 'Farm lane'
    ROAM = 'ROAM', 'Roaming'
    
class SideChoice(models.TextChoices):
    BLUE = 'BLUE', 'Blue side'
    RED = 'RED', 'Red side'

class DraftChoice(models.TextChoices):
    BAN = 'BAN', 'Ban'
    PICK = 'PICK', 'Pick'
    
# Core models
class Hero(models.Model):
    name_en=models.CharField(max_length=100, verbose_name='Hero Name (English)')
    name_vn=models.CharField(max_length=100, verbose_name='Hero Name (Vietnamese)')
    name_ppl=models.CharField(max_length=100, verbose_name='Hero Name (Popular)')
    name_url=models.URLField(verbose_name='Hero Image URL (if needed)')
    
    class Meta:
        verbose_name = 'Hero'
        verbose_name_plural = 'Heroes'
        
    def __str__(self):
        return self.name_ppl
    
class Team(models.Model):
    name=models.CharField(max_length=100, verbose_name='Team Name')
    logo_url=models.URLField(verbose_name='Team Logo URL (if needed)')
    region=models.CharField(max_length=100, verbose_name='Team Region')
    
    class Meta:
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        
    def __str__(self):
        return self.name
    
class Player(models.Model):
    name=models.CharField(max_length=100, verbose_name='Player Name')
    ign=models.CharField(max_length=100, verbose_name='In-Game Name')
    team=models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    default_role=models.CharField(max_length=100, verbose_name='Default Role')
    signature_hero=models.ForeignKey(Hero, on_delete=models.SET_NULL, null=True, blank=True, related_name='signature_players')
    
    class Meta:
        verbose_name = 'Player'
        verbose_name_plural = 'Players'
        
    def __str__(self):
        return self.ign
    
# Match and tournament models

class Tournament(models.Model):
    name=models.CharField(max_length=100, verbose_name='Tournament Name')
    game_version=models.CharField(max_length=10, choices=GameVersionChoice.choices, verbose_name='Game Version')
    year=models.IntegerField(verbose_name='Year')
    
    class Meta:
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'
        
    def __str__(self):
        return f"{self.name} {self.year}"
    
class Match(models.Model):
    tournament=models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    # Home team set as left side, away team set as right side for consistency
    home_team_ref=models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team_ref=models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    
    home_team_score=models.IntegerField(verbose_name='Home Team Score')
    away_team_score=models.IntegerField(verbose_name='Away Team Score')
    
    stage=models.CharField(max_length=100, verbose_name='Match Stage (e.g. Group Stage, Quarterfinals)')
    date=models.DateField(verbose_name='Game Date')

    class Meta:
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'
    
    def __str__(self):
        return f"{self.home_team_ref} vs {self.away_team_ref} - {self.tournament}"
    
class Game(models.Model):
    match=models.ForeignKey(Match, on_delete=models.CASCADE, related_name='games')
    game_number=models.IntegerField(verbose_name='Game Number (e.g. Game 1, Game 2)')
    duration=models.CharField(max_length=20, verbose_name='Game Duration')
    blue_side_team=models.ForeignKey(Team, on_delete=models.CASCADE, related_name='blue_side_games')
    red_side_team=models.ForeignKey(Team, on_delete=models.CASCADE, related_name='red_side_games')
    winner_side=models.CharField(max_length=10, choices=SideChoice.choices, verbose_name='Winning Side')
    mvp_player=models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='mvp_games', verbose_name='MVP Player')
    
    class Meta:
        verbose_name = 'Game'
        verbose_name_plural = 'Games'

    def __str__(self):
        return f"{self.match} - Game {self.game_number}"


class GameDraft(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='drafts', verbose_name='Game')
    slot = models.IntegerField(verbose_name='Draft Slot (1-20)')
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE, null=True, blank=True, related_name='drafts', verbose_name='Hero')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='drafts', verbose_name='Team')
    action_type = models.CharField(max_length=10, choices=DraftChoice.choices, verbose_name='Action Type')

    class Meta:
        verbose_name = 'Game Draft'
        verbose_name_plural = 'Game Drafts'
        unique_together = ('game', 'slot')
        ordering = ['slot']

    def __str__(self):
        return f"Game {self.game.game_number} - Slot {self.slot}: {self.action_type} {self.hero} by {self.team}"


class GameLineup(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='lineups', verbose_name='Game')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups', verbose_name='Player')
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE, related_name='lineups', verbose_name='Hero')
    lane = models.CharField(max_length=10, choices=LaneChoice.choices, verbose_name='Lane')
    kills = models.IntegerField(default=0, verbose_name='Kills')
    deaths = models.IntegerField(default=0, verbose_name='Deaths')
    assists = models.IntegerField(default=0, verbose_name='Assists')
    gold = models.IntegerField(default=0, verbose_name='Gold')
    is_mvp = models.BooleanField(default=False, verbose_name='Is MVP')

    class Meta:
        verbose_name = 'Game Lineup'
        verbose_name_plural = 'Game Lineups'
        unique_together = (('game', 'player'), ('game', 'hero'))

    def __str__(self):
        return f"Game {self.game.game_number} - {self.player} ({self.lane}) playing {self.hero}"
