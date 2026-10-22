import pytest

from src.ingest.wikipedia_parse import (
    clean_team,
    extract_blocks,
    parse_date,
    parse_matches,
    parse_score,
)

SAMPLE = """
{{rugbybox
|date = 6 December 2025
|time = 13:00
|home = (1 BP) [[Saracens F.C.|Saracens]] {{flagicon|ENG}}
|score = 47–10
|report = [https://www.epcrugby.com/champions-cup/matches/288362/commentary Report]
|away = {{flagicon|FRA}} [[ASM Clermont Auvergne|Clermont]]
|try1 = [[Lucio Cinti|Cinti]] (2) 9' c, 30' c
|stadium = [[Barnet Copthall|StoneX Stadium]], London
}}
----
{{rugbybox
|date = 7 December 2025
|time = 16:15
|home = (1 BP) [[Stade Toulousain|Toulouse]] {{flagicon|FRA}}
|score = 56–19
|away = {{flagicon|RSA}} [[Sharks (rugby union)|Sharks]] (1 BP)
|stadium = [[Stade Ernest-Wallon]], Toulouse
}}
"""


def test_extracts_blocks_despite_nested_templates():
    assert len(extract_blocks(SAMPLE)) == 2


def test_team_names_cleaned_from_flags_and_bonus_points():
    assert clean_team("(1 BP) [[Saracens F.C.|Saracens]] {{flagicon|ENG}}") == "Saracens"
    assert clean_team("{{flagicon|RSA}} [[Sharks (rugby union)|Sharks]] (1 BP)") == "Sharks"
    assert clean_team("[[Leinster]]") == "Leinster"


def test_score_parsing_handles_dashes_and_unplayed():
    assert parse_score("47–10") == (47, 10)
    assert parse_score("47-10") == (47, 10)
    assert parse_score("v") == (None, None)
    assert parse_score("") == (None, None)


def test_parse_matches_end_to_end():
    rows = parse_matches(SAMPLE, season="2025-26", competition="Champions Cup")
    assert rows[0]["date"] == "2025-12-06"
    assert (rows[0]["home_team"], rows[0]["away_team"]) == ("Saracens", "Clermont")
    assert (rows[0]["home_score"], rows[0]["away_score"]) == (47, 10)
    assert (rows[1]["home_team"], rows[1]["away_team"]) == ("Toulouse", "Sharks")


def test_bad_date_raises():
    with pytest.raises(ValueError, match="Could not parse date"):
        parse_date("sometime in December")
