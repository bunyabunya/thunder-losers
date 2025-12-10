import streamlit as st
from espn_api.football import League

st.set_page_config(page_title="2025 Losers Bracket", layout="centered")

st.title("2025 Fantasy Losers Bracket")
st.markdown("Live standings for the bottom 4 — who’s buying the trophy?")

# === YOUR LEAGUE INFO ===
LEAGUE_ID = 1590064
YEAR = 2025
ESPN_S2 = st.secrets.get("ESPN_S2", "paste-your-espn_s2-here-if-not-using-secrets")
SWID = st.secrets.get("SWID", "{BFC87BD7-0D5C-4FCD-AE92-2450A5C8ABEF}")

# Initialize league
try:
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
except Exception as e:
    st.error("Could not load league. Check your ESPN_S2 and SWID cookies (they expire!).")
    st.stop()

current_week = league.current_week
completed_weeks = current_week - 1

if completed_weeks < 14:
    st.error("Week 14 not completed yet. Come back later!")
    st.stop()

st.write(f"Data through completed Week **{completed_weeks}** (Week {current_week} is next)\n")

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

st.subheader("Bottom 4 teams after Week 14")
for rank, entry in enumerate(standings_after_wk14[-4:], 1):
    t = entry['team']
    st.write(f"{rank}. **{t.team_name}** ({entry['wins']}-{entry['losses']}-{entry['ties']}, PF: {entry['points_for']:.2f})")

# === 2. Losers bracket scores ===
actual_completed = len(league.teams[0].scores)
bracket_scores = {}
for team in bottom4:
    bracket_scores[team] = sum(team.scores[14:min(17, actual_completed)])

all_tied_in_bracket = len(set(bracket_scores[t] for t in bottom4)) == 1

if all_tied_in_bracket:
    st.warning("ALL 4 TEAMS ARE TIED in losers bracket points! Using Week 14 standings as tiebreaker.")
    final_order = [entry['team'] for entry in standings_after_wk14[-4:]]
else:
    final_order = sorted(bottom4, key=lambda t: bracket_scores[t], reverse=True)  # highest first

# === 3. Final ranking ===
st.subheader("Final Losers Bracket Ranking (Weeks 15–17)" + 
            (" ← TIED → Week 14 tiebreaker applied" if all_tied_in_bracket else ""))

for pos, team in enumerate(final_order, 1):
    pts = bracket_scores[team]
    if pos == 4:
        st.error(f"{pos}. **{team.team_name}** — {pts:.2f} pts  ← DEAD LAST")
    else:
        st.write(f"{pos}. **{team.team_name}** — {pts:.2f} pts")

# === 4. Points needed ===
last_team        = final_order[-1]
second_last_team = final_order[-2]

points_needed = 0.0
if not all_tied_in_bracket:
    gap = bracket_scores[second_last_team] - bracket_scores[last_team]
    points_needed = max(0, gap + 0.01)

remaining_weeks = max(0, 17 - actual_completed)

st.markdown("---")
if remaining_weeks > 0:
    st.info(f"**{last_team.team_name}** needs **{points_needed:.2f}** more points in the next {remaining_weeks} week(s) to escape dead last.")
else:
    if all_tied_in_bracket:
        st.success(f"Bracket over — tied! Week 14 tiebreaker says **{last_team.team_name}** is officially DEAD LAST.")
    elif points_needed > 0:
        st.success(f"Bracket complete! **{last_team.team_name}** is your 2025 DEAD LAST champion.")
    else:
        st.success(f"Somehow {last_team.team_name} survived...")

st.caption("Refreshes automatically · Share this link with the league!")