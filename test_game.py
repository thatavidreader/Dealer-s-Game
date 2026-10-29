import pytest

from game import apply_penalties, new_players, outcome, parse_number, resolve_round


def test_target_and_winner():
    result = resolve_round({"a": 10, "b": 20, "c": 90}, "standard")
    assert result["average"] == pytest.approx(40)
    assert result["target"] == pytest.approx(28)
    assert result["winners"] == ["b"]
    assert result["penalties"] == {"a": 1, "b": 0, "c": 1}


def test_tie_has_multiple_winners():
    result = resolve_round({"a": 30, "b": 40, "c": 65, "d": 65}, "standard")
    assert result["target"] == pytest.approx(35)
    assert sorted(result["winners"]) == ["a", "b"]
    assert result["penalties"] == {"a": 0, "b": 0, "c": 1, "d": 1}


def test_double_penalty():
    result = resolve_round({"a": 10, "b": 20, "c": 90}, "double_penalty")
    assert result["penalties"] == {"a": 2, "b": 0, "c": 2}


def test_no_duplicates_excludes_duplicate_pickers():
    result = resolve_round({"a": 20, "b": 20, "c": 90}, "no_duplicates")
    assert result["winners"] == ["c"]
    assert result["penalties"] == {"a": 1, "b": 1, "c": 0}


def test_no_duplicates_everyone_duplicated():
    result = resolve_round({"a": 50, "b": 50}, "no_duplicates")
    assert result["winners"] == []
    assert result["penalties"] == {"a": 1, "b": 1}


def test_exact_hit_doubles_penalty():
    result = resolve_round({"a": 12, "b": 20, "c": 20}, "exact_hit")
    assert result["winners"] == ["a"]
    assert result["exact"]
    assert result["penalties"] == {"a": 0, "b": 2, "c": 2}


def test_exact_hit_not_triggered_when_missed():
    result = resolve_round({"a": 10, "b": 20, "c": 90}, "exact_hit")
    assert not result["exact"]
    assert result["penalties"] == {"a": 1, "b": 0, "c": 1}


def test_lives_never_negative():
    players = new_players("me")
    apply_penalties(players, {"me": 99})
    assert players[0]["lives"] == 0


def test_outcome():
    players = new_players("me")
    assert outcome(players) is None
    for p in players[1:]:
        p["lives"] = 0
    assert outcome(players) == "victory"
    players[0]["lives"] = 0
    assert outcome(players) == "defeat"


@pytest.mark.parametrize(
    "raw,expected",
    [("50", 50), (" 0 ", 0), ("100", 100), ("101", None), ("-1", None), ("abc", None), ("", None), ("5.5", None), ("5.0", 5)],
)
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected
