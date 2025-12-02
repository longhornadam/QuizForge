import json

import pytest

parser_mod = pytest.importorskip("dev.newspec_engine.parser")
packager_mod = pytest.importorskip("dev.newspec_engine.packager")
parse_news_json = parser_mod.parse_news_json
package_quiz = packager_mod.package_quiz


def _build_payload(**overrides):
    base = {
        "version": "3.0-json",
        "title": "Sample",
        "items": [
            {
                "id": "stim1",
                "type": "STIMULUS",
                "prompt": "Context block",
                "points": 10,  # should be stripped
            },
            {
                "id": "q1",
                "type": "MC",
                "prompt": "Prompt?",
                "choices": [
                    {"text": "A", "correct": True},
                    {"text": "B", "correct": False},
                ],
            },
            {
                "id": "end1",
                "type": "STIMULUS_END",
                "prompt": "",
                "points": 5,  # should be stripped
            },
        ],
        "rationales": [
            {"item_id": "stim1", "correct": "noop", "distractor": "noop"},
            {"item_id": "q1", "correct": "Because A is correct.", "distractor": "B misses key detail."},
        ],
    }
    base.update(overrides)
    return base


def test_parse_handles_chatty_wrapping_and_strips_points_from_stimulus():
    payload = _build_payload()
    text = f"Hello!\n<QUIZFORGE_JSON>\n{json.dumps(payload)}\n</QUIZFORGE_JSON>\nThanks!"
    quiz = parse_news_json(text)

    assert quiz.version == "3.0-json"
    assert quiz.title == "Sample"
    assert len(quiz.items) == 3
    assert "points" not in quiz.items[0]  # STIMULUS stripped
    assert "points" not in quiz.items[2]  # STIMULUS_END stripped


def test_packager_filters_rationales_for_structural_items_only():
    payload = parse_news_json(f"<QUIZFORGE_JSON>{json.dumps(_build_payload())}</QUIZFORGE_JSON>")
    packaged = package_quiz(payload)

    assert len(packaged.rationales) == 1
    assert packaged.rationales[0].item_id == "q1"
    assert packaged.items[0]["type"] == "STIMULUS"
    assert packaged.items[1]["type"] == "MC"


def test_metadata_passes_through_untouched():
    payload = _build_payload(
        metadata={"extensions": {"world": {"layout": "corridor", "q_per_room": 1}}},
    )
    payload["items"][1]["metadata"] = {"foo": "bar", "nested": {"hint": "keep"}}
    text = f"<QUIZFORGE_JSON>{json.dumps(payload)}</QUIZFORGE_JSON>"
    quiz = parse_news_json(text)
    assert quiz.metadata["extensions"]["world"]["layout"] == "corridor"
    assert quiz.items[1]["metadata"]["nested"]["hint"] == "keep"


def test_missing_tags_raises():
    with pytest.raises(ValueError):
        parse_news_json("No tags here")
