import os
import re
import sys
import argparse
from datetime import datetime

# Setup Django Environment
import os
import sys
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hev.settings')
import django
django.setup()

from django.db import transaction
from django.db.models import Q
from db.models import Hero, Team, Player, Tournament, Match, Game, GameDraft, GameLineup, SideChoice, DraftChoice, LaneChoice

def split_params(template_content):
    """Split mediawiki template parameters by '|', respecting nested double braces."""
    params = []
    pos = 0
    n = len(template_content)
    depth = 0
    current = []
    while pos < n:
        if template_content[pos:pos+2] == '{{':
            depth += 1
            current.append('{{')
            pos += 2
        elif template_content[pos:pos+2] == '}}':
            depth -= 1
            current.append('}}')
            pos += 2
        elif template_content[pos] == '|' and depth == 0:
            params.append(''.join(current).strip())
            current = []
            pos += 1
        else:
            current.append(template_content[pos])
            pos += 1
    if current:
        params.append(''.join(current).strip())
    return params

def parse_params(params):
    """Parse list of param strings into a dict of key-value and index-value pairs."""
    parsed = {}
    for param in params:
        if '=' in param:
            key, val = param.split('=', 1)
            parsed[key.strip()] = val.strip()
        else:
            parsed[len(parsed)] = param.strip()
    return parsed

def parse_nested_template(template_str):
    """Parse a single nested template like {{TeamOpponent|Agfox|score=2}}."""
    if not (template_str.startswith('{{') and template_str.endswith('}}')):
        return None
    inner = template_str[2:-2].strip()
    params = split_params(inner)
    if not params:
        return None
    name = params[0]
    parsed_params = parse_params(params[1:])
    return {'name': name, 'params': parsed_params}

def find_templates(text):
    """Extract all top-level curly brace templates from raw text."""
    templates = []
    pos = 0
    n = len(text)
    while pos < n:
        start = text.find('{{', pos)
        if start == -1:
            break
        depth = 1
        i = start + 2
        while i < n - 1 and depth > 0:
            if text[i:i+2] == '{{':
                depth += 1
                i += 2
            elif text[i:i+2] == '}}':
                depth -= 1
                i += 2
            else:
                i += 1
        if depth == 0:
            templates.append(text[start:i])
            pos = i
        else:
            pos = start + 2
    return templates

def get_or_create_hero(name):
    """Find a Hero by any of its name variants, or create a new one."""
    if not name:
        return None
    name = name.strip()
    hero = Hero.objects.filter(Q(name_ppl__iexact=name) | Q(name_en__iexact=name) | Q(name_vn__iexact=name)).first()
    if not hero:
        hero = Hero.objects.create(name_ppl=name, name_en=name, name_vn=name)
        print(f"[Hero] Created hero: {name}")
    return hero

def get_or_create_team(name):
    """Find or create a Team by name."""
    if not name:
        return None
    name = name.strip()
    team, created = Team.objects.get_or_create(name=name, defaults={'region': 'Unknown'})
    if created:
        print(f"[Team] Created team: {name}")
    return team

def get_or_create_player(ign, team):
    """Find or create a Player by IGN and Team."""
    if not ign or not team:
        return None
    ign = ign.strip()
    player = Player.objects.filter(ign__iexact=ign, team=team).first()
    if not player:
        player = Player.objects.create(ign=ign, name=ign, team=team, default_role='ROAM')
        print(f"[Player] Created player: {ign} for team {team.name}")
    return player

def parse_date(date_str):
    """Parse date from various formats, default to today."""
    if not date_str:
        return datetime.now().date()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%B %d, %Y - %H:%M', '%B %d, %Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date()
    return datetime.now().date()

@transaction.atomic
def ingest_match(match_data, tournament):
    """Process parsed match template parameters and ingest into DB."""
    # Resolve opponents
    opp1_raw = match_data.get('opponent1', '')
    opp2_raw = match_data.get('opponent2', '')
    
    opp1_tpl = parse_nested_template(opp1_raw)
    opp2_tpl = parse_nested_template(opp2_raw)
    
    if not opp1_tpl or not opp2_tpl:
        print("[Error] Invalid opponent formats in match")
        return
        
    team1_name = opp1_tpl['params'].get(0, 'Team 1')
    team2_name = opp2_tpl['params'].get(0, 'Team 2')
    
    team1_score = int(opp1_tpl['params'].get('score', 0))
    team2_score = int(opp2_tpl['params'].get('score', 0))
    
    team1 = get_or_create_team(team1_name)
    team2 = get_or_create_team(team2_name)
    
    date_val = parse_date(match_data.get('date', ''))
    stage = match_data.get('stage', 'Group Stage')
    
    # Create Match record
    match = Match.objects.create(
        tournament=tournament,
        home_team_ref=team1,
        away_team_ref=team2,
        home_team_score=team1_score,
        away_team_score=team2_score,
        stage=stage,
        date=date_val
    )
    print(f"\n[Match] Created Match: {team1.name} ({team1_score}) vs {team2.name} ({team2_score}) on {date_val}")
    
    # Find maps
    map_index = 1
    while True:
        map_key = f"map{map_index}"
        if map_key not in match_data:
            break
            
        map_raw = match_data[map_key]
        map_tpl = parse_nested_template(map_raw)
        
        if map_tpl and map_tpl['name'].lower() == 'map':
            ingest_game(match, map_index, map_tpl['params'], team1, team2)
            
        map_index += 1

def ingest_game(match, game_number, game_params, team1, team2):
    """Process a single game map parameters and ingest draft and lineup."""
    winner_num = game_params.get('winner', '1')
    duration = game_params.get('length', '00:00')
    team1side = game_params.get('team1side', 'blue').lower()
    
    # Resolve winner and side team mappings
    if team1side == 'blue':
        blue_team = team1
        red_team = team2
        winner_side = SideChoice.BLUE if winner_num == '1' else SideChoice.RED
    else:
        blue_team = team2
        red_team = team1
        winner_side = SideChoice.RED if winner_num == '1' else SideChoice.BLUE
        
    game = Game.objects.create(
        match=match,
        game_number=game_number,
        duration=duration,
        blue_side_team=blue_team,
        red_side_team=red_team,
        winner_side=winner_side
    )
    print(f"  [Game] Created Game {game_number}: Blue={blue_team.name}, Red={red_team.name}, Winner={winner_side}")
    
    # --- Process Drafts (Bans/Picks) ---
    # Draft Slots deterministic mapping:
    # Team 1 (first listed opponent) and Team 2 (second listed opponent)
    t1_bans = [game_params.get(f"t1b{i}") for i in range(1, 6) if game_params.get(f"t1b{i}")]
    t2_bans = [game_params.get(f"t2b{i}") for i in range(1, 6) if game_params.get(f"t2b{i}")]
    t1_picks = [game_params.get(f"t1h{i}") for i in range(1, 6) if game_params.get(f"t1h{i}")]
    t2_picks = [game_params.get(f"t2h{i}") for i in range(1, 6) if game_params.get(f"t2h{i}")]
    
    # Let's map slot numbers chronologically (1 to 20)
    # T1 side defines Blue side slots if team1side == blue, otherwise Red side slots
    t1_is_blue = (team1side == 'blue')
    
    # Map Bans
    for idx, hero_name in enumerate(t1_bans):
        hero = get_or_create_hero(hero_name)
        # Assign slot: Blue bans are odd slots (1, 3, 11, 13, 15), Red bans are even slots (2, 4, 12, 14, 16)
        slot = (idx * 2 + 1) if t1_is_blue else (idx * 2 + 2)
        if idx >= 2: # Phase 2 bans are offset
            slot += 6
        GameDraft.objects.create(game=game, slot=slot, hero=hero, team=team1, action_type=DraftChoice.BAN)
        
    for idx, hero_name in enumerate(t2_bans):
        hero = get_or_create_hero(hero_name)
        slot = (idx * 2 + 2) if t1_is_blue else (idx * 2 + 1)
        if idx >= 2:
            slot += 6
        GameDraft.objects.create(game=game, slot=slot, hero=hero, team=team2, action_type=DraftChoice.BAN)
        
    # Map Picks
    for idx, hero_name in enumerate(t1_picks):
        hero = get_or_create_hero(hero_name)
        # Assign picking slot order
        # Standard MOBA order mapping fallback:
        # Blue picks: 5, 8, 9, 17, 18
        # Red picks: 6, 7, 10, 19, 20
        blue_slots = [5, 8, 9, 17, 18]
        red_slots = [6, 7, 10, 19, 20]
        slot_list = blue_slots if t1_is_blue else red_slots
        slot = slot_list[idx] if idx < len(slot_list) else (21 + idx)
        GameDraft.objects.create(game=game, slot=slot, hero=hero, team=team1, action_type=DraftChoice.PICK)
        
    for idx, hero_name in enumerate(t2_picks):
        hero = get_or_create_hero(hero_name)
        blue_slots = [5, 8, 9, 17, 18]
        red_slots = [6, 7, 10, 19, 20]
        slot_list = red_slots if t1_is_blue else blue_slots
        slot = slot_list[idx] if idx < len(slot_list) else (21 + idx)
        GameDraft.objects.create(game=game, slot=slot, hero=hero, team=team2, action_type=DraftChoice.PICK)

    # --- Process Lineups ---
    # Lanes layout
    lanes = [LaneChoice.CLASH, LaneChoice.JUNGLE, LaneChoice.MID, LaneChoice.FARM, LaneChoice.ROAM]
    
    # Process Team 1 Lineup
    mvp_player_obj = None
    for i in range(1, 6):
        player_name = game_params.get(f"t1p{i}")
        hero_name = game_params.get(f"t1h{i}")
        
        # If no player names are specified in map wikitext, fallback to default team roster
        if not player_name:
            team_players = list(Player.objects.filter(team=team1))
            if len(team_players) >= i:
                player_obj = team_players[i-1]
            else:
                player_obj = get_or_create_player(f"{team1.name}_Player_{i}", team1)
        else:
            player_obj = get_or_create_player(player_name, team1)
            
        hero_obj = get_or_create_hero(hero_name)
        if not hero_obj:
            continue
            
        lane_str = game_params.get(f"t1p{i}lane", lanes[i-1]).upper()
        # Clean lane string to match choices
        lane = LaneChoice.ROAM
        for ch in LaneChoice.choices:
            if ch[0] in lane_str or lane_str in ch[0]:
                lane = ch[0]
                break
                
        kills = int(game_params.get(f"t1p{i}k", 0))
        deaths = int(game_params.get(f"t1p{i}d", 0))
        assists = int(game_params.get(f"t1p{i}a", 0))
        is_mvp = game_params.get(f"t1p{i}mvp", 'false').lower() == 'true'
        
        lineup_entry = GameLineup.objects.create(
            game=game,
            player=player_obj,
            hero=hero_obj,
            lane=lane,
            kills=kills,
            deaths=deaths,
            assists=assists
        )
        if is_mvp:
            mvp_player_obj = player_obj
            
    # Process Team 2 Lineup
    for i in range(1, 6):
        player_name = game_params.get(f"t2p{i}")
        hero_name = game_params.get(f"t2h{i}")
        
        if not player_name:
            team_players = list(Player.objects.filter(team=team2))
            if len(team_players) >= i:
                player_obj = team_players[i-1]
            else:
                player_obj = get_or_create_player(f"{team2.name}_Player_{i}", team2)
        else:
            player_obj = get_or_create_player(player_name, team2)
            
        hero_obj = get_or_create_hero(hero_name)
        if not hero_obj:
            continue
            
        lane_str = game_params.get(f"t2p{i}lane", lanes[i-1]).upper()
        lane = LaneChoice.ROAM
        for ch in LaneChoice.choices:
            if ch[0] in lane_str or lane_str in ch[0]:
                lane = ch[0]
                break
                
        kills = int(game_params.get(f"t2p{i}k", 0))
        deaths = int(game_params.get(f"t2p{i}d", 0))
        assists = int(game_params.get(f"t2p{i}a", 0))
        is_mvp = game_params.get(f"t2p{i}mvp", 'false').lower() == 'true'
        
        lineup_entry = GameLineup.objects.create(
            game=game,
            player=player_obj,
            hero=hero_obj,
            lane=lane,
            kills=kills,
            deaths=deaths,
            assists=assists
        )
        if is_mvp:
            mvp_player_obj = player_obj
            
    # If MVP player found, update Game record
    if mvp_player_obj:
        game.mvp_player = mvp_player_obj
        game.save()
        print(f"    [Game MVP] MVP of the game is {mvp_player_obj.ign}")

def parse_file(file_path, tournament_name, game_version, year):
    """Read wikitext file, parse templates, and ingest match lists."""
    print(f"Starting ingestion for Tournament '{tournament_name}' ({game_version} - {year})")
    
    tournament = get_or_create_tournament(tournament_name, game_version, year)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    templates = find_templates(text)
    print(f"Found {len(templates)} top-level templates to parse.")
    
    matches_count = 0
    for tpl_str in templates:
        tpl = parse_nested_template(tpl_str)
        if tpl and tpl['name'].lower() == 'match':
            ingest_match(tpl['params'], tournament)
            matches_count += 1
            
    print(f"\nIngested {matches_count} matches successfully!")

def get_or_create_tournament(name, game_version, year):
    """Find or create a Tournament record."""
    tournament, created = Tournament.objects.get_or_create(
        name=name,
        game_version=game_version,
        year=year
    )
    if created:
        print(f"[Tournament] Created tournament: {name} ({year})")
    return tournament

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse Liquipedia wikitext and ingest eSports match data.')
    parser.add_argument('file', help='Path to the wikitext file')
    parser.add_argument('--tournament', required=True, help='Name of the Tournament')
    parser.add_argument('--version', choices=['VGVD', 'HOK', 'AOV'], default='HOK', help='Game version (VGVD, HOK, AOV)')
    parser.add_argument('--year', type=int, default=datetime.now().year, help='Year of the Tournament')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)
        
    parse_file(args.file, args.tournament, args.version, args.year)
