from django.contrib import admin
from .models import Hero, Team, Player, Tournament, Match, Game, GameDraft, GameLineup

# --- Inlines ---

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 5
    fields = ('ign', 'name', 'default_role', 'signature_hero')


class GameInline(admin.TabularInline):
    model = Game
    extra = 3
    show_change_link = True
    fields = ('game_number', 'duration', 'blue_side_team', 'red_side_team', 'winner_side')


class GameDraftInline(admin.TabularInline):
    model = GameDraft
    extra = 20
    ordering = ('slot',)
    fields = ('slot', 'team', 'hero', 'action_type')


class GameLineupInline(admin.TabularInline):
    model = GameLineup
    extra = 10
    fields = ('player', 'hero', 'lane', 'kills', 'deaths', 'assists')


# --- Model Admins ---

@admin.register(Hero)
class HeroAdmin(admin.ModelAdmin):
    list_display = ('name_ppl', 'name_en', 'name_vn', 'name_url')
    search_fields = ('name_ppl', 'name_en', 'name_vn')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'logo_url')
    search_fields = ('name', 'region')
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('ign', 'name', 'team', 'default_role', 'signature_hero')
    list_filter = ('team', 'default_role')
    search_fields = ('ign', 'name')


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_version', 'year')
    list_filter = ('game_version', 'year')
    search_fields = ('name',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'stage', 'home_team_score', 'away_team_score', 'date')
    list_filter = ('tournament', 'date')
    search_fields = ('home_team_ref__name', 'away_team_ref__name', 'tournament__name')
    inlines = [GameInline]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'match', 'game_number', 'duration', 'winner_side')
    list_filter = ('winner_side', 'match__tournament')
    search_fields = ('match__home_team_ref__name', 'match__away_team_ref__name')
    inlines = [GameDraftInline, GameLineupInline]


@admin.register(GameDraft)
class GameDraftAdmin(admin.ModelAdmin):
    list_display = ('game', 'slot', 'team', 'hero', 'action_type')
    list_filter = ('action_type', 'team')
    search_fields = ('game__match__home_team_ref__name', 'game__match__away_team_ref__name', 'hero__name_ppl')


@admin.register(GameLineup)
class GameLineupAdmin(admin.ModelAdmin):
    list_display = ('game', 'player', 'hero', 'lane', 'kills', 'deaths', 'assists')
    list_filter = ('lane',)
    search_fields = ('game__match__home_team_ref__name', 'game__match__away_team_ref__name', 'player__ign', 'hero__name_ppl')
