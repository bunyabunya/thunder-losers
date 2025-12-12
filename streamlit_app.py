import streamlit as st
from espn_api.football import League

st.set_page_config(page_title="Losers Bracket 2025", layout="wide")

# === CONFIGURATION ===
LEAGUE_ID = 1590064
YEAR = 2025
ESPN_S2 = st.secrets["ESPN_S2"]      # Use secrets for security
SWID = st.secrets["SWID"]

# Initialize league
try:
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
except Exception as e:
    st.error("Failed to connect to ESPN. Check your ESPN_S2 and SWID cookies.")
    st.stop()

current_week = league.current_week
completed_weeks = current_week - 1

if completed_weeks < 14:
    st.error("Week 14 not completed yet. Cannot determine bottom 4.")
    st.stop()

st.write(f"Data through completed Week {completed_weeks} (Week {current_week} is next / in progress)\n")

# === 1. Standings after Week 14 ===
standings_after_wk14 = []
for team in league.teams:
    outcomes = team.outcomes[:14]
    scores   = team.scores[:14]
    
    wins   = outcomes.count('W')
    losses = outcomes.count('L')
    ties   = outcomes.count('T')
    points_for = sum(scores)
    
    win_pct = (wins + 0.5 * ties) / 14
    
    standings_after_wk14.append({
        'team': team,
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'win_pct': win_pct,
        'points_for': points_for
    })

standings_after_wk14.sort(key=lambda x: (x['win_pct'], x['points_for']), reverse=True)
bottom4 = [entry['team'] for entry in standings_after_wk14[-4:]]

st.write("**Bottom 4 teams after Week 14 (regular season tiebreakers):**")
for rank, entry in enumerate(standings_after_wk14[-4:], 1):
    t = entry['team']
    st.write(f"{rank}. {t.team_name} ({entry['wins']}-{entry['losses']}-{entry['ties']}, PF: {entry['points_for']:.2f})")
st.write("")

# === 2. Losers bracket scores (Weeks 15–17) ===
@st.cache_data(ttl=60)  # Auto-refresh every 60 seconds
def calculate_bracket_scores():
    bracket_scores = {team: 0.0 for team in bottom4}

    # Add completed bracket weeks (from team.scores — finalized)
    bracket_start_idx = 14
    actual_completed = len(league.teams[0].scores)
    completed_bracket_weeks = max(0, actual_completed - 14)

    for team in bottom4:
        bracket_scores[team] += sum(team.scores[bracket_start_idx : bracket_start_idx + completed_bracket_weeks])

    # Add LIVE score for current week if it's in the bracket (Week 15–17)
    live_message = ""
    if 15 <= current_week <= 17:
        try:
            matchups = league.box_scores(current_week)
            for matchup in matchups:
                if matchup.home_team in bottom4:
                    bracket_scores[matchup.home_team] += matchup.home_score
                if matchup.away_team in bottom4:
                    bracket_scores[matchup.away_team] += matchup.away_score
            live_message = f"Added LIVE scores for current Week {current_week}\n"
        except Exception as e:
            live_message = f"Could not fetch live scores for Week {current_week}: {e}\n"

    return bracket_scores, live_message

bracket_scores, live_message = calculate_bracket_scores()

if live_message:
    if "Added LIVE" in live_message:
        st.success(live_message)
    else:
        st.warning(live_message)

# Detect total tie
all_tied_in_bracket = len(set(bracket_scores.values())) == 1

if all_tied_in_bracket:
    st.warning("All 4 teams have identical losers bracket totals!")
    st.write("Falling back to Week 14 regular-season standings order...\n")
    final_order = [entry['team'] for entry in standings_after_wk14[-4:]]
    tiebreaker_used = True
else:
    final_order = sorted(bottom4, key=lambda t: bracket_scores[t], reverse=True)
    tiebreaker_used = False

# === 3. Final losers bracket ranking ===
title = "Final Losers Bracket Ranking (Weeks 15–17)"
if tiebreaker_used:
    title += "  ← TIED → using Week 14 standings as tiebreaker"
st.subheader(title)
st.write("-" * 50)

for pos, team in enumerate(final_order, 1):
    bracket_pts = bracket_scores[team]
    st.code(f"{pos}. {team.team_name:<25} {bracket_pts:>8.2f} pts")

# === 4. Points needed ===
last_team        = final_order[-1]
second_last_team = final_order[-2]

points_needed = 0.0
if not tiebreaker_used:
    gap = bracket_scores[second_last_team] - bracket_scores[last_team]
    points_needed = max(0, gap + 0.01)

remaining_weeks = max(0, 17 - current_week + 1)

st.markdown("\n" + "="*60)
if current_week <= 17:
    st.info(f"→ {last_team.team_name} needs at least {points_needed:.2f} more points "
            f"over the next {remaining_weeks} week(s) to pass {second_last_team.team_name} "
            "(assuming others score 0 more).")
    if 15 <= current_week <= 17:
        st.info("   Scores include LIVE updates for the current week!")
else:
    if points_needed > 0:
        st.error(f"Bracket is over! {last_team.team_name} finished {points_needed:.2f} points behind "
                 f"{second_last_team.team_name} and is officially dead last.")
    else:
        st.success(f"Bracket is complete and {last_team.team_name} is safe from dead last "
                   f"(or tied and saved by Week 14 tiebreaker).")

if tiebreaker_used:
    st.warning(f"\nBecause of the total tie, Week 14 standings were used → "
               f"{last_team.team_name} is officially last place for the season.")

st.markdown("="*60)

st.caption("🔄 Updates automatically every minute • Live scoring during games • Share this link!")