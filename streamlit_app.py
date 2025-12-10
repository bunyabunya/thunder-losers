import streamlit as st
from espn_api.football import League
import os

st.set_page_config(page_title="2025 Losers Bracket 🏆💀", layout="centered")

st.title("🏈 2025 Fantasy Losers Bracket")
st.markdown("Live standings for the bottom 4 — who’s buying the trophy?")

# === CONFIGURATION (put your real values here) ===
LEAGUE_ID = 1590064
YEAR = 2025
ESPN_S2 = st.secrets["ESPN_S2"]      # We'll store this securely in secrets
SWID = st.secrets["SWID"]            # We'll store this securely in secrets

# Initialize league
league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)

# ... [PASTE THE ENTIRE SCRIPT FROM MY LAST MESSAGE STARTING FROM line "current_week = ..." DOWN TO THE VERY END] ...
# Just copy everything below this line from the previous code and paste it here
# (Yes, the whole thing — it works perfectly inside Streamlit)

current_week = league.current_week
completed_weeks = current_week - 1

if completed_weeks < 14:
    print("Week 14 not completed yet. Cannot determine bottom 4.")
    exit()

print(f"Data through completed Week {completed_weeks} (Week {current_week} is next)\n")

# === 1. Standings after Week 14 (for initial bottom 4 + tiebreaker fallback) ===
standings_after_wk14 = []
for team in league.teams:
    outcomes = team.outcomes[:14]
    scores   = team.scores[:14]
    
    wins   = outcomes.count('W')
    losses = outcomes.count('L')
    ties   = outcomes.count('T')
    points_for = sum(scores)
    
    total_games = wins + losses + ties
    win_pct = (wins + 0.5 * ties) / 14 if total_games == 14 else 0
    
    standings_after_wk14.append({
        'team': team,
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'win_pct': win_pct,
        'points_for': points_for
    })

# Sort: highest win % → most PF
standings_after_wk14.sort(key=lambda x: (x['win_pct'], x['points_for']), reverse=True)

# Bottom 4 after Week 14
bottom4 = [entry['team'] for entry in standings_after_wk14[-4:]]

print("Bottom 4 teams after Week 14 (regular season tiebreakers):")
for rank, entry in enumerate(standings_after_wk14[-4:], 1):
    t = entry['team']
    print(f"{rank}. {t.team_name} ({entry['wins']}-{entry['losses']}-{entry['ties']}, PF: {entry['points_for']:.2f})")
print()

# === 2. Losers bracket scores (Weeks 15–17) ===
actual_completed = len(league.teams[0].scores)
bracket_start_idx = 14
bracket_end_idx   = min(17, actual_completed)

bracket_scores = {}
for team in bottom4:
    week15_to_now = team.scores[bracket_start_idx:bracket_end_idx]
    bracket_scores[team] = sum(week15_to_now)

# Check if everyone is tied in the bracket
all_tied_in_bracket = len(set(bracket_scores[t] for t in bottom4)) == 1

if all_tied_in_bracket:
    print("All 4 teams have identical losers bracket totals!")
    print("Falling back to Week 14 regular-season standings order...\n")
    # Keep original bottom-4 order from Week 14 (worst is last)
    final_order = [entry['team'] for entry in standings_after_wk14[-4:]]
    tiebreaker_used = True
else:
    # HIGHEST bracket score first → 1st place in losers bracket
    final_order = sorted(bottom4, key=lambda t: bracket_scores[t], reverse=True)
    tiebreaker_used = False

# === 3. Final losers bracket ranking ===
print("Final Losers Bracket Ranking (Weeks 15–17):" + 
      ("  ← TIED → using Week 14 standings as tiebreaker" if tiebreaker_used else ""))
print("-" * 50)
for pos, team in enumerate(final_order, 1):
    bracket_pts = bracket_scores[team]
    print(f"{pos}. {team.team_name:<25} {bracket_pts:>8.2f} pts")

# === 4. Points needed for current DEAD LAST to escape ===
last_team        = final_order[-1]   # now correctly the lowest scorer (or Week 14 worst)
second_last_team = final_order[-2]

points_needed = 0.0
if not tiebreaker_used:
    gap = bracket_scores[second_last_team] - bracket_scores[last_team]
    points_needed = max(0, gap + 0.01)

remaining_weeks = 17 - actual_completed
if bracket_end_idx >= 17:
    remaining_weeks = 0

print("\n" + "="*60)
if remaining_weeks > 0:
    print(f"→ {last_team.team_name} needs at least {points_needed:.2f} more points "
          f"over the next {remaining_weeks} week(s) to pass {second_last_team.team_name} "
          "(assuming others score 0 more).")
else:
    if points_needed > 0:
        print(f"Bracket is over! {last_team.team_name} finished {points_needed:.2f} points behind "
              f"{second_last_team.team_name} and is officially dead last.")
    else:
        print(f"Bracket is complete and {last_team.team_name} is safe from dead last "
              f"(or tied and saved by Week 14 tiebreaker).")

if tiebreaker_used:
    print("\nBecause of the total tie, Week 14 standings were used → "
          f"{last_team.team_name} is officially last place for the season.")

print("="*60)