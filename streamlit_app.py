import streamlit as st
from espn_api.football import League

st.set_page_config(page_title="2025 Losers Bracket • LIVE", layout="centered")

st.title("2025 Fantasy Losers Bracket")
st.markdown("**LIVE real-time standings** — updates during games • Weeks 15–17 decider")

# === CONFIG ===
LEAGUE_ID = 1590064
YEAR = 2025
ESPN_S2 = st.secrets["ESPN_S2"]
SWID = st.secrets["SWID"]

try:
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
except:
    st.error("Could not load league — check your ESPN_S2 and SWID (they expire!).")
    st.stop()

current_week = league.current_week
completed_weeks = current_week - 1

if completed_weeks < 14:
    st.error("Week 14 not finished yet — check back later!")
    st.stop()

st.write(f"**Regular season:** through Week 14 • **Bracket:** Weeks 15–17")
if 15 <= current_week <= 17:
    st.success(f"Live scoring active for Week {current_week}")

# === 1. Bottom 4 after Week 14 ===
standings_wk14 = []
for team in league.teams:
    outcomes = team.outcomes[:14]
    scores = team.scores[:14]
    wins = outcomes.count('W')
    losses = outcomes.count('L')
    ties = outcomes.count('T')
    pf = sum(scores)
    win_pct = (wins + 0.5 * ties) / 14
    standings_wk14.append({'team': team, 'win_pct': win_pct, 'pf': pf})

standings_wk14.sort(key=lambda x: (x['win_pct'], x['pf']), reverse=True)
bottom4 = [e['team'] for e in standings_wk14[-4:]]

st.subheader("Bottom 4 after Week 14")
for i, e in enumerate(standings_wk14[-4:], 1):
    t = e['team']
    st.write(f"{i}. **{t.team_name}**")

# === 2. LIVE Losers bracket totals ===
@st.cache_data(ttl=90)  # Refresh every 90 seconds
def get_live_bracket_totals():
    scores = {team: 0.0 for team in bottom4}

    # Add completed bracket weeks (from finalized scores)
    actual_completed = len(league.teams[0].scores)
    completed_bracket = max(0, actual_completed - 14)
    for team in bottom4:
        scores[team] += sum(team.scores[14:14 + completed_bracket])

    # Add LIVE current week if it's Week 15, 16, or 17
    if 15 <= current_week <= 17:
        try:
            matchups = league.box_scores(current_week)
            for m in matchups:
                if m.home_team in bottom4:
                    scores[m.home_team] += m.home_score
                if m.away_team in bottom4:
                    scores[m.away_team] += m.away_score
        except:
            pass  # No live data yet

    return scores

bracket_scores = get_live_bracket_totals()

all_tied = len(set(bracket_scores.values())) == 1

if all_tied:
    st.warning("ALL 4 TEAMS CURRENTLY TIED! Using Week 14 standings as tiebreaker")
    final_order = [e['team'] for e in standings_wk14[-4:]]
else:
    final_order = sorted(bottom4, key=lambda t: bracket_scores[t], reverse=True)

# === 3. Final Ranking ===
st.subheader("Live Losers Bracket Ranking (Weeks 15–17)" +
            (" ← TIED → Week 14 tiebreaker applied" if all_tied else ""))

for pos, team in enumerate(final_order, 1):
    pts = bracket_scores[team]
    if pos == 4:
        st.error(f"{pos}. **{team.team_name}** — **{pts:.2f}** pts  ← DEAD LAST")
    elif pos == 1:
        st.success(f"{pos}. **{team.team_name}** — {pts:.2f} pts  ← King of the Losers")
    else:
        st.write(f"{pos}. **{team.team_name}** — {pts:.2f} pts")

# === 4. Points needed ===
last = final_order[-1]
second = final_order[-2]
gap = bracket_scores[second] - bracket_scores[last]
points_needed = max(0, gap + 0.01) if not all_tied else 0

remaining = max(0, 17 - current_week + 1)

st.markdown("---")
if current_week <= 17:
    if points_needed > 0:
        st.info(f"**{last.team_name}** needs **{points_needed:.2f}** more points over the next {remaining} week(s) to escape dead last!")
    else:
        st.info(f"**{last.team_name}** is currently safe… for now.")
else:
    if all_tied:
        st.balloons()
        st.success(f"SEASON OVER — ALL TIED! Week 14 says **{last.team_name}** is your official DEAD LAST!")
    else:
        st.success(f"Bracket complete! Your 2025 DEAD LAST champion is… **{last.team_name}**")

st.caption("Updates automatically • Live during games • Share this link with the league!")