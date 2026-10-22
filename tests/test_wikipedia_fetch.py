from src.ingest.wikipedia_fetch import safe_filename


def test_safe_filename_strips_unsafe_characters():
    name = safe_filename("2025–26 European Rugby Champions Cup pool stage")
    assert name.endswith(".wikitext")
    assert "/" not in name and " " not in name
