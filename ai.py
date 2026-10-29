import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

from game import MULTIPLIER, TWISTS, clamp

load_dotenv()

MODEL = os.environ.get("GAME_MODEL", "openai/gpt-oss-20b")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
TIMEOUT = float(os.environ.get("GAME_TIMEOUT", "30"))


def headers():
    return {"Authorization": f"Bearer {os.environ.get('LLM_API_KEY', '')}"}

RULES = (
    "Rules of the game: every player secretly picks an integer from 0 to 100. "
    f"The average of all picks is multiplied by {MULTIPLIER} to give the target. "
    "The player closest to the target wins the round and everyone else loses a life. "
    "A player with no lives left is eliminated."
)

FALLBACK_LINES = {
    "opening": "Welcome to the table. Pick a number, and try not to be the one who is furthest from the truth.",
    "round_result": "The target has been set and the lives have been counted. Let us see who learns from it.",
    "victory": "Impressive. You out-thought every one of them. The table is yours.",
    "defeat": "Your last life is gone. The table does not forgive hesitation.",
}

def model_status():
    if not os.environ.get("LLM_API_KEY"):
        return "nokey"
    try:
        response = requests.get(f"{BASE_URL}/models", headers=headers(), timeout=5)
        if response.status_code in (401, 403):
            return "badkey"
        response.raise_for_status()
        names = [m["id"] for m in response.json().get("data", [])]
    except Exception:
        return "offline"
    return "ready" if MODEL in names else "missing"


def ask_llm(system, prompt, max_tokens=300, json_mode=False):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.9,
    }
    if "gpt-oss" in MODEL:
        payload["reasoning_effort"] = "low"
        payload["max_tokens"] = max_tokens + 400
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    for attempt in range(2):
        response = requests.post(
            f"{BASE_URL}/chat/completions", json=payload, headers=headers(), timeout=TIMEOUT
        )
        if response.status_code == 429 and attempt == 0:
            time.sleep(2)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in reply")
    return json.loads(match.group())


def history_text(history):
    if not history:
        return "No rounds have been played yet."
    lines = []
    for entry in history:
        picks = ", ".join(f"{name} {number}" for name, number in entry["picks"].items())
        winners = ", ".join(entry["winners"]) or "nobody"
        lines.append(
            f"Round {entry['round']} (rule: {entry['twist']}): picks [{picks}], "
            f"average {entry['average']:.1f}, target {entry['target']:.1f}, winner {winners}"
        )
    return "\n".join(lines)


def lives_text(lives):
    return ", ".join(f"{name}: {count} lives" for name, count in lives.items())


def fallback_number(history):
    if history:
        base = history[-1]["target"]
        return clamp(random.gauss(base, 10))
    return random.randint(15, 45)


def opponent_move(name, persona, lives, history, twist):
    system = (
        f"You are {name}, {persona}. You are a contestant in a high-stakes number game. "
        f"{RULES} "
        "Reason about what the other players are likely to pick, then choose your number. "
        'Reply with only a JSON object: {"number": <integer 0-100>, "thought": "<one sentence in character, max 25 words>"}'
    )
    prompt = (
        f"Current extra rule: {TWISTS[twist]}\n"
        f"Lives: {lives_text(lives)}\n"
        f"History:\n{history_text(history)}\n"
        "Choose your number for this round."
    )
    for _ in range(2):
        try:
            data = extract_json(ask_llm(system, prompt, max_tokens=150, json_mode=True))
            number = clamp(round(float(data["number"])))
            thought = str(data.get("thought", "")).strip()[:200]
            return number, thought, True
        except Exception:
            continue
    return fallback_number(history), "...", False


def dealer_line(event, context=""):
    system = (
        "You are the Dealer, the calm, theatrical and slightly menacing host of a deadly number game. "
        f"{RULES} "
        "Reply with one to three short sentences. React only to the facts you are given. "
        "Never recalculate or change any numbers or results."
    )
    prompts = {
        "opening": "Open the game and greet the new player.",
        "round_result": "Comment on the round that just finished.",
        "victory": "The human player has won. Give a closing speech.",
        "defeat": "The human player has been eliminated. Give a closing speech.",
    }
    prompt = f"{prompts[event]}\nFacts:\n{context}" if context else prompts[event]
    try:
        text = ask_llm(system, prompt, max_tokens=150).strip()
        if text:
            return text, True
    except Exception:
        pass
    return FALLBACK_LINES[event], False


def choose_twist(round_no, history, lives):
    menu = "\n".join(f"- {key}: {desc}" for key, desc in TWISTS.items())
    system = (
        "You are the Dealer of a deadly number game. Before each round you may announce an extra rule. "
        f"{RULES} "
        'Reply with only a JSON object: {"twist": "<one key from the menu>", "announcement": "<one dramatic sentence announcing it>"}'
    )
    prompt = (
        f"Menu of rules:\n{menu}\n"
        f"Upcoming round: {round_no}\n"
        f"Lives: {lives_text(lives)}\n"
        f"History:\n{history_text(history)}\n"
        "Choose the rule for the upcoming round."
    )
    try:
        data = extract_json(ask_llm(system, prompt, max_tokens=150, json_mode=True))
        twist = data["twist"]
        if twist in TWISTS:
            announcement = str(data.get("announcement", "")).strip() or TWISTS[twist]
            return twist, announcement, True
    except Exception:
        pass
    twist = random.choice(list(TWISTS))
    return twist, TWISTS[twist], False


def all_opponent_moves(opponents, lives, history, twist):
    with ThreadPoolExecutor(max_workers=len(opponents)) as pool:
        futures = [
            pool.submit(opponent_move, p["name"], p["persona"], lives, history, twist)
            for p in opponents
        ]
        return [f.result() for f in futures]
