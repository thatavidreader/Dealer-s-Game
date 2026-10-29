from html import escape as esc

import streamlit as st

import ai
from game import (
    MAX_NUM,
    MIN_NUM,
    MULTIPLIER,
    PERSONAS,
    START_LIVES,
    TWISTS,
    alive,
    apply_penalties,
    new_players,
    outcome,
    parse_number,
    resolve_round,
)

st.set_page_config(
    page_title="The Dealer's Game",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TWIST_NAMES = {
    "standard": "Standard",
    "double_penalty": "Double penalty",
    "no_duplicates": "No duplicates",
    "exact_hit": "Exact hit",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800&family=Hanken+Grotesk:ital,wght@0,400;0,500;1,400&family=Martian+Mono:wght@400;500&display=swap');
:root {
  --bg: #0b0b0c;
  --card: #ece4d3;
  --ink: #17150f;
  --text: #e9e4d8;
  --muted: #8a857a;
  --line: #262529;
  --accent: #d63a2f;
  --display: 'Big Shoulders Display', sans-serif;
  --body: 'Hanken Grotesk', sans-serif;
  --mono: 'Martian Mono', monospace;
}
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"] { display: none; }
html, body, [data-testid="stApp"] { background: var(--bg); }
[data-testid="stApp"], [data-testid="stApp"] p, [data-testid="stApp"] label { font-family: var(--body); color: var(--text); }
.block-container { max-width: 1360px; padding: 2.4rem 3.2rem 3rem; }
[data-testid="stSidebar"] { background: #121214; border-right: 1px solid var(--line); }
[data-testid="stHorizontalBlock"] { align-items: flex-start; }
[data-testid="stColumn"]:first-child, [data-testid="column"]:first-child { position: sticky; top: 2rem; }
.wordmark { font-family: var(--display); font-weight: 800; text-transform: uppercase; font-size: 3.4rem; line-height: 0.9; letter-spacing: 0.01em; margin: 0 0 6px; }
.wordmark.xl { font-size: 5.6rem; margin-bottom: 10px; }
.wordmark span { color: var(--accent); }
.meta { font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 18px; }
.label { font-family: var(--mono); font-size: 0.64rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
.label b { color: var(--accent); font-weight: 500; margin-left: 8px; }
.hand { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
.card { background: var(--card); color: var(--ink); min-height: 98px; padding: 10px 12px 12px; display: flex; flex-direction: column; justify-content: space-between; border-radius: 3px; position: relative; }
.card .corner { display: flex; flex-direction: column; align-items: flex-start; line-height: 1; }
.card .rank { font-family: var(--display); font-weight: 800; font-size: 1.5rem; }
.card .suit { font-size: 1rem; color: var(--ink); margin-top: 2px; }
.card .suit.red { color: var(--accent); }
.card .tag { position: absolute; top: 12px; right: 12px; font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.1em; }
.card .cname { font-family: var(--display); font-weight: 700; font-size: 1.25rem; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }
.card .pips { display: flex; gap: 4px; }
.card .pips i { display: block; flex: 1; height: 6px; background: var(--ink); }
.card .pips i.off { background: rgba(23,21,15,0.16); }
.card.dead { background: transparent; border: 1px solid var(--line); color: var(--muted); }
.card.dead .suit, .card.dead .rank { color: var(--muted); }
.card.dead .cname { text-decoration: line-through; }
.card.dead .pips i, .card.dead .pips i.off { background: var(--line); }
.rule-name { font-family: var(--display); font-weight: 800; font-size: 2rem; text-transform: uppercase; line-height: 1; margin: 4px 0 4px; }
.rule-desc { color: var(--muted); font-size: 0.9rem; line-height: 1.45; margin-bottom: 12px; max-width: 420px; }
.say { margin: 22px 0 6px; max-width: 760px; }
.say p { margin: 8px 0 0; font-size: 1.12rem; line-height: 1.6; }
.thought { margin: 10px 0 0; font-size: 0.95rem; line-height: 1.5; color: #bdb8ab; font-style: italic; max-width: 760px; }
.thought .label { font-style: normal; color: var(--text); }
.round { border-top: 1px solid var(--line); margin-top: 44px; padding-top: 20px; }
.round:first-of-type { margin-top: 0; }
.round-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; }
.round-head .rn { font-family: var(--display); font-weight: 800; font-size: 1.5rem; text-transform: uppercase; letter-spacing: 0.04em; }
.stats { display: flex; gap: 56px; margin-bottom: 16px; }
.stats .k { display: block; font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 2px; }
.stats .v { font-family: var(--display); font-weight: 800; font-size: 2.6rem; line-height: 1; }
.feat .stats .v { font-size: 5rem; }
.stats .v.hot { color: var(--accent); }
table.t { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
table.t th, table.t td { border: none; border-bottom: 1px solid var(--line); background: transparent; }
table.t th { text-align: left; font-family: var(--mono); font-size: 0.62rem; font-weight: 400; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); padding: 8px 0; }
table.t td { padding: 10px 0; font-size: 0.98rem; }
table.t td.n { font-family: var(--mono); font-size: 0.85rem; }
table.t th.r, table.t td.r { text-align: right; }
table.t tr.win td { color: var(--accent); }
.note { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); margin: 0 0 16px; }
.end .big { font-family: var(--display); font-weight: 800; font-size: 3.2rem; text-transform: uppercase; line-height: 0.95; }
.end.lose .big { color: var(--accent); }
.end .sub { color: var(--muted); margin: 8px 0 22px; }
.mult { font-family: var(--display); font-weight: 800; font-size: clamp(5rem, 9vw, 8.5rem); line-height: 0.9; color: var(--accent); margin: 0 0 30px; }
.steps { list-style: none; padding: 0; margin: 0; }
.steps li { display: flex; gap: 18px; padding: 12px 0; border-top: 1px solid var(--line); font-size: 1.05rem; }
.steps li span { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); padding-top: 5px; }
[data-testid="stForm"] { border: none; padding: 0; }
[data-testid="InputInstructions"] { display: none; }
.stTextInput [data-baseweb="input"], .stTextInput [data-baseweb="base-input"] { background: transparent; border: none; border-radius: 0; height: auto; min-height: 0; margin-bottom: 8px; }
.stTextInput input { background: transparent; border: none; border-bottom: 2px solid var(--text); border-radius: 0; color: var(--text); font-family: var(--display); font-weight: 700; font-size: 2rem; line-height: 1.2; height: auto; padding: 12px 2px 10px; }
.stTextInput input::placeholder { color: #4a4740; }
.stTextInput input:focus { border-bottom-color: var(--accent); box-shadow: none; }
.stButton button, [data-testid="stFormSubmitButton"] button { width: 100%; background: var(--accent); border: 1px solid var(--accent); border-radius: 0; padding: 12px 20px; }
.stButton button p, [data-testid="stFormSubmitButton"] button p { color: var(--text) !important; font-family: var(--display); font-weight: 700; font-size: 1.15rem; letter-spacing: 0.16em; text-transform: uppercase; }
.stButton button:hover, .stButton button:focus:not(:active), .stButton button:active, [data-testid="stFormSubmitButton"] button:hover, [data-testid="stFormSubmitButton"] button:focus:not(:active), [data-testid="stFormSubmitButton"] button:active { background: var(--card); border-color: var(--card); }
.stButton button:hover p, .stButton button:focus p, .stButton button:active p, [data-testid="stFormSubmitButton"] button:hover p, [data-testid="stFormSubmitButton"] button:focus p, [data-testid="stFormSubmitButton"] button:active p { color: var(--ink) !important; }
[data-testid="stAlert"] { border-radius: 0; }
</style>
"""


@st.cache_data(ttl=60)
def provider_status():
    return ai.model_status()


def facts_for_dealer(entry, players):
    picks = ", ".join(f"{n} picked {v}" for n, v in entry["picks"].items())
    lost = ", ".join(f"{n} -{c}" for n, c in entry["penalties"].items() if c) or "nobody"
    winners = ", ".join(entry["winners"]) or "nobody"
    lives = ", ".join(f"{p['name']} {p['lives']}" for p in players)
    return (
        f"Round {entry['round']}, rule: {entry['twist']}. {picks}. "
        f"Average {entry['average']:.2f}, target {entry['target']:.2f}. "
        f"Winner: {winners}. Lives lost: {lost}. Lives now: {lives}."
    )


def start_game(name):
    players = new_players(name)
    opening, ok = ai.dealer_line("opening")
    st.session_state.update(
        players=players,
        history=[],
        round_no=1,
        twist="standard",
        announcement=TWISTS["standard"],
        phase="playing",
        opening=opening,
        closing=None,
        notices=[] if ok else ["dealer opening"],
    )


def play_round(number):
    state = st.session_state
    players = state.players
    twist = state.twist
    notices = []

    living = alive(players)
    opponents = [p for p in living if not p["human"]]
    lives = {p["name"]: p["lives"] for p in living}
    human = next(p for p in players if p["human"])

    moves = ai.all_opponent_moves(opponents, lives, state.history, twist)
    picks = {human["name"]: number}
    thoughts = {}
    for player, (value, thought, ok) in zip(opponents, moves):
        picks[player["name"]] = value
        thoughts[player["name"]] = thought
        if not ok:
            notices.append(f"{player['name'].lower()}'s move")

    result = resolve_round(picks, twist)
    apply_penalties(players, result["penalties"])

    entry = {
        "round": state.round_no,
        "twist": twist,
        "picks": picks,
        "thoughts": thoughts,
        "average": result["average"],
        "target": result["target"],
        "winners": result["winners"],
        "penalties": result["penalties"],
        "exact": result["exact"],
    }

    final = outcome(players)
    line, ok = ai.dealer_line(final or "round_result", facts_for_dealer(entry, players))
    if not ok:
        notices.append("dealer commentary")
    entry["dealer"] = line
    state.history.append(entry)

    if final:
        state.phase = "over"
        state.closing = final
    else:
        state.round_no += 1
        next_lives = {p["name"]: p["lives"] for p in alive(players)}
        next_twist, announcement, ok = ai.choose_twist(state.round_no, state.history, next_lives)
        if not ok:
            notices.append("rule selection")
        state.twist = next_twist
        state.announcement = announcement

    state.notices = notices


def wordmark(meta, big=False):
    st.markdown(
        f'<div class="wordmark{" xl" if big else ""}">The<br>Dealer&rsquo;s<br><span>Game</span></div>'
        f'<div class="meta">{esc(meta)}</div>',
        unsafe_allow_html=True,
    )


def say(speaker, text):
    st.markdown(
        f'<div class="say"><div class="label">&#9830; {esc(speaker)}<b>AI</b></div><p>{esc(text)}</p></div>',
        unsafe_allow_html=True,
    )


def thought(speaker, text):
    st.markdown(
        f'<p class="thought"><span class="label">{esc(speaker)}</span><span class="label"><b>AI</b></span> '
        f'&ldquo;{esc(text)}&rdquo;</p>',
        unsafe_allow_html=True,
    )


SUITS = [("&#9830;&#xFE0E;", True), ("&#9829;&#xFE0E;", True), ("&#9827;&#xFE0E;", False), ("&#9824;&#xFE0E;", False)]


def hand(players):
    cards = []
    for index, p in enumerate(players):
        suit, red = SUITS[index % len(SUITS)]
        pips = "".join(f'<i class="{"" if k < p["lives"] else "off"}"></i>' for k in range(START_LIVES))
        cls = "card"
        if p["human"]:
            cls += " you"
        if p["lives"] <= 0:
            cls += " dead"
        tag = "YOU" if p["human"] else "AI"
        cards.append(
            f'<div class="{cls}"><div class="corner"><span class="rank">{esc(p["name"][0].upper())}</span>'
            f'<span class="suit{" red" if red else ""}">{suit}</span></div><span class="tag">{tag}</span>'
            f'<div><div class="cname">{esc(p["name"])}</div><div class="pips">{pips}</div></div></div>'
        )
    st.markdown(f'<div class="hand">{"".join(cards)}</div>', unsafe_allow_html=True)


def entry_block(entry, featured=False):
    rows = []
    for name, number in entry["picks"].items():
        won = name in entry["winners"]
        result = "Wins" if won else f"&minus;{entry['penalties'][name]}"
        cls = ' class="win"' if won else ""
        rows.append(
            f'<tr{cls}><td>{esc(name)}</td><td class="n r">{number}</td>'
            f'<td class="n r">{abs(number - entry["target"]):.2f}</td><td class="n r">{result}</td></tr>'
        )
    html = (
        f'<div class="round{" feat" if featured else ""}">'
        f'<div class="round-head"><span class="rn">Round {entry["round"]:02d}</span>'
        f'<span class="label">{esc(TWIST_NAMES[entry["twist"]])}</span></div>'
        '<div class="stats">'
        f'<div><span class="k">Average</span><span class="v">{entry["average"]:.2f}</span></div>'
        f'<div><span class="k">Target &times; {MULTIPLIER}</span><span class="v hot">{entry["target"]:.2f}</span></div>'
        "</div>"
        '<table class="t"><thead><tr><th>Player</th><th class="r">Pick</th><th class="r">Off by</th><th class="r"></th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    for name, text in entry["thoughts"].items():
        thought(name, text)
    say("Dealer", entry["dealer"])


def rules_panel():
    with st.sidebar:
        st.markdown('<div class="label">How to play</div>', unsafe_allow_html=True)
        st.markdown(
            f"Everyone picks a whole number from {MIN_NUM} to {MAX_NUM}. "
            f"The average is multiplied by **{MULTIPLIER}** to give the target. "
            "Closest to the target wins the round. Everyone else loses a life. "
            f"You each start with {START_LIVES}. "
            "The dealer may add an extra rule every round. "
            "Dialogue and opponent picks marked AI are generated by a language model."
        )


def play_screen():
    state = st.session_state
    left, right = st.columns([5, 8], gap="large")

    with left:
        wordmark(f"Round {state.round_no:02d}" if state.phase == "playing" else "Game over")
        hand(state.players)

        if state.phase == "playing":
            st.markdown(
                '<div class="label">Rule for this round</div>'
                f'<div class="rule-name">{esc(TWIST_NAMES[state.twist])}</div>'
                f'<div class="rule-desc">{esc(state.announcement)}</div>',
                unsafe_allow_html=True,
            )
            with st.form("pick", clear_on_submit=True):
                raw = st.text_input(
                    "Your number",
                    placeholder=f"{MIN_NUM} to {MAX_NUM}",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Lock in")
            if submitted:
                number = parse_number(raw)
                if number is None:
                    st.error(f"Enter a whole number between {MIN_NUM} and {MAX_NUM}.")
                else:
                    with st.spinner("Waiting for the others"):
                        play_round(number)
                    st.rerun()
        else:
            won = state.closing == "victory"
            st.markdown(
                f'<div class="end {"win" if won else "lose"}">'
                f'<div class="big">{"You survived" if won else "Eliminated"}</div>'
                f'<div class="sub">{"Every opponent is out." if won else "You ran out of lives."}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Play again"):
                start_game(state.players[0]["name"])
                st.rerun()

    with right:
        if state.notices:
            st.markdown(
                f'<p class="note">Model unavailable, fallback used for: {esc(", ".join(state.notices))}.</p>',
                unsafe_allow_html=True,
            )
        for index, entry in enumerate(reversed(state.history)):
            entry_block(entry, featured=index == 0)
        say("Dealer", state.opening)


def start_screen():
    st.markdown(
        "<style>.block-container{max-width:1080px;padding-top:15vh}</style>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1, 1], gap="large")
    with left:
        wordmark("Four players. One target.", big=True)
        with st.form("name"):
            name = st.text_input("Your name", placeholder="Your name", label_visibility="collapsed")
            begin = st.form_submit_button("Sit down")
        if begin:
            cleaned = name.strip()
            if not cleaned:
                st.error("Enter a name to sit down.")
            elif cleaned.lower() in (n.lower() for n in PERSONAS):
                st.error("That name belongs to one of the other players.")
            else:
                start_game(cleaned[:20])
                st.rerun()
    with right:
        st.markdown(
            f'<div class="mult">&times;{MULTIPLIER}</div>'
            '<ul class="steps">'
            f"<li><span>01</span>Everyone picks a whole number from {MIN_NUM} to {MAX_NUM}.</li>"
            f"<li><span>02</span>The average is multiplied by {MULTIPLIER}. That is the target.</li>"
            "<li><span>03</span>Closest to the target survives. The rest lose a life.</li>"
            "</ul>",
            unsafe_allow_html=True,
        )


st.markdown(CSS, unsafe_allow_html=True)
rules_panel()

status = provider_status()
messages = {
    "nokey": "LLM_API_KEY is not set. Add it to the .env file and restart.",
    "badkey": "The API key was rejected. Check LLM_API_KEY in .env.",
    "missing": f"The model {ai.MODEL} is not available on this account. Change GAME_MODEL in .env.",
    "offline": "Cannot reach the AI provider. Check your connection.",
}
if status != "ready":
    st.error(messages[status])

if "phase" not in st.session_state:
    start_screen()
else:
    play_screen()
