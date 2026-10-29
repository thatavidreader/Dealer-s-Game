MULTIPLIER = 0.7
START_LIVES = 5
MIN_NUM = 0
MAX_NUM = 100

PERSONAS = {
    "Kaito": "a cold, analytical strategist who assumes everyone reasons several levels deep and tries to out-think them",
    "Rex": "an impulsive gambler who trusts gut feeling and likes bold, unexpected numbers",
    "Mina": "a paranoid, suspicious player who assumes the others are conspiring and second-guesses every move",
}

TWISTS = {
    "standard": "No extra rule. The closest number to the target wins.",
    "double_penalty": "Every loser loses 2 lives instead of 1.",
    "no_duplicates": "Anyone who picks the same number as another player cannot win and loses a life.",
    "exact_hit": "If the winner hits the rounded target exactly, every other player loses 2 lives.",
}


def clamp(value):
    return max(MIN_NUM, min(MAX_NUM, int(value)))


def parse_number(raw):
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    if value != int(value) or not MIN_NUM <= value <= MAX_NUM:
        return None
    return int(value)


def new_players(human_name):
    players = [{"name": human_name, "persona": None, "human": True, "lives": START_LIVES}]
    for name, persona in PERSONAS.items():
        players.append({"name": name, "persona": persona, "human": False, "lives": START_LIVES})
    return players


def alive(players):
    return [p for p in players if p["lives"] > 0]


def resolve_round(picks, twist, multiplier=MULTIPLIER):
    average = sum(picks.values()) / len(picks)
    target = average * multiplier

    counts = {}
    for number in picks.values():
        counts[number] = counts.get(number, 0) + 1

    eligible = dict(picks)
    if twist == "no_duplicates":
        eligible = {name: n for name, n in picks.items() if counts[n] == 1}

    winners = []
    if eligible:
        distances = {name: round(abs(n - target), 9) for name, n in eligible.items()}
        best = min(distances.values())
        winners = [name for name, d in distances.items() if d == best]

    penalty = 2 if twist == "double_penalty" else 1
    exact = twist == "exact_hit" and len(winners) == 1 and picks[winners[0]] == round(target)
    if exact:
        penalty = 2

    penalties = {name: 0 if name in winners else penalty for name in picks}
    return {
        "average": average,
        "target": target,
        "winners": winners,
        "penalties": penalties,
        "exact": exact,
    }


def apply_penalties(players, penalties):
    for player in players:
        player["lives"] = max(0, player["lives"] - penalties.get(player["name"], 0))


def outcome(players):
    human = next(p for p in players if p["human"])
    if human["lives"] <= 0:
        return "defeat"
    if not any(not p["human"] and p["lives"] > 0 for p in players):
        return "victory"
    return None
