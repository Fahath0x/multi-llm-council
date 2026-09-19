"""
Unit tests for pure (no-network) functions in council.py and storage.py.

These tests run fully offline — no OpenRouter API key needed.
"""

import sys
import os
import json
import tempfile
import pytest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Bootstrap import path so 'backend' resolves from the project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def _import_council():
    from backend.council import (
        parse_ranking_from_text,
        calculate_aggregate_rankings,
        calculate_consensus_metrics,
        get_persona,
        COUNCIL_PERSONAS,
    )
    return (
        parse_ranking_from_text,
        calculate_aggregate_rankings,
        calculate_consensus_metrics,
        get_persona,
        COUNCIL_PERSONAS,
    )


# ===========================================================================
# 1. parse_ranking_from_text
# ===========================================================================
class TestParseRankingFromText:
    """Tests for the ranking text parser used in Stage 2 evaluation."""

    def setup_method(self):
        (self.parse, self.calc_agg, self.calc_consensus,
         self.get_persona, self.personas) = _import_council()

    def test_standard_numbered_format(self):
        text = (
            "Response A was great.\nResponse B missed key details.\n\n"
            "FINAL RANKING:\n1. Response A\n2. Response B\n3. Response C\n"
        )
        result = self.parse(text)
        assert result == ["Response A", "Response B", "Response C"]

    def test_partial_ranking_two_items(self):
        text = "FINAL RANKING:\n1. Response B\n2. Response A"
        result = self.parse(text)
        assert result == ["Response B", "Response A"]

    def test_fallback_no_final_ranking_header(self):
        """Without FINAL RANKING: header, falls back to any Response X patterns."""
        text = "I think Response C is best, then Response A, then Response B."
        result = self.parse(text)
        assert result.index("Response C") < result.index("Response A")
        assert result.index("Response A") < result.index("Response B")

    def test_none_input_returns_empty(self):
        assert self.parse(None) == []

    def test_empty_string_returns_empty(self):
        assert self.parse("") == []

    def test_non_string_returns_empty(self):
        assert self.parse(42) == []  # type: ignore[arg-type]

    def test_ranking_with_trailing_text(self):
        text = (
            "FINAL RANKING:\n1. Response B\n2. Response A\n3. Response C\n\n"
            "Overall a close call."
        )
        result = self.parse(text)
        assert result[:3] == ["Response B", "Response A", "Response C"]

    def test_ranking_with_markdown_bold(self):
        """Models sometimes bold the label — regex should still find Response X."""
        text = "FINAL RANKING:\n1. **Response A**\n2. **Response B**"
        result = self.parse(text)
        assert "Response A" in result
        assert "Response B" in result

    def test_single_model_ranking(self):
        text = "FINAL RANKING:\n1. Response A"
        result = self.parse(text)
        assert result == ["Response A"]

    def test_large_label_count(self):
        items = [f"{i+1}. Response {chr(65+i)}" for i in range(6)]  # A-F
        text = "FINAL RANKING:\n" + "\n".join(items)
        result = self.parse(text)
        assert len(result) == 6
        assert result[0] == "Response A"
        assert result[-1] == "Response F"


# ===========================================================================
# 2. calculate_aggregate_rankings
# ===========================================================================
class TestCalculateAggregateRankings:
    def setup_method(self):
        (self.parse, self.calc_agg, self.calc_consensus,
         self.get_persona, self.personas) = _import_council()

    def _make_stage2(self, rankings_texts):
        return [
            {"model": f"model_{i}", "ranking": text, "parsed_ranking": []}
            for i, text in enumerate(rankings_texts)
        ]

    def test_unanimous_winner(self):
        label_to_model = {
            "Response A": "openai/gpt-4o",
            "Response B": "anthropic/claude-3.7",
        }
        stage2 = self._make_stage2([
            "FINAL RANKING:\n1. Response A\n2. Response B",
            "FINAL RANKING:\n1. Response A\n2. Response B",
            "FINAL RANKING:\n1. Response A\n2. Response B",
        ])
        result = self.calc_agg(stage2, label_to_model)
        assert result[0]["model"] == "openai/gpt-4o"
        assert result[0]["average_rank"] == 1.0

    def test_mixed_opinions_averages_correctly(self):
        label_to_model = {"Response A": "model-a", "Response B": "model-b"}
        stage2 = self._make_stage2([
            "FINAL RANKING:\n1. Response A\n2. Response B",
            "FINAL RANKING:\n1. Response B\n2. Response A",
        ])
        result = self.calc_agg(stage2, label_to_model)
        ranks = {r["model"]: r["average_rank"] for r in result}
        assert ranks["model-a"] == 1.5
        assert ranks["model-b"] == 1.5

    def test_empty_stage2_returns_empty(self):
        result = self.calc_agg([], {"Response A": "model-a"})
        assert result == []

    def test_unknown_label_ignored(self):
        label_to_model = {"Response A": "model-a"}
        stage2 = self._make_stage2(
            ["FINAL RANKING:\n1. Response Z\n2. Response A"]  # Z is unknown
        )
        result = self.calc_agg(stage2, label_to_model)
        assert len(result) == 1
        assert result[0]["model"] == "model-a"
        assert result[0]["average_rank"] == 2.0

    def test_three_models_sorted_correctly(self):
        label_to_model = {
            "Response A": "model-a",
            "Response B": "model-b",
            "Response C": "model-c",
        }
        stage2 = self._make_stage2([
            "FINAL RANKING:\n1. Response C\n2. Response A\n3. Response B",
            "FINAL RANKING:\n1. Response C\n2. Response A\n3. Response B",
        ])
        result = self.calc_agg(stage2, label_to_model)
        assert result[0]["model"] == "model-c"
        assert result[1]["model"] == "model-a"
        assert result[2]["model"] == "model-b"


# ===========================================================================
# 3. calculate_consensus_metrics
# ===========================================================================
class TestCalculateConsensusMetrics:
    def setup_method(self):
        (self.parse, self.calc_agg, self.calc_consensus,
         self.get_persona, self.personas) = _import_council()

    def _make_stage2(self, rankings_texts):
        return [
            {"model": f"model_{i}", "ranking": text, "parsed_ranking": []}
            for i, text in enumerate(rankings_texts)
        ]

    def test_empty_inputs_return_defaults(self):
        result = self.calc_consensus([], {}, [])
        assert result["score"] == 100
        assert result["tier"] == "unanimous"
        assert result["total_voters"] == 0

    def test_unanimous_consensus_high_score(self):
        label_to_model = {"Response A": "m-a", "Response B": "m-b"}
        stage2 = self._make_stage2([
            "FINAL RANKING:\n1. Response A\n2. Response B",
            "FINAL RANKING:\n1. Response A\n2. Response B",
            "FINAL RANKING:\n1. Response A\n2. Response B",
        ])
        agg = self.calc_agg(stage2, label_to_model)
        result = self.calc_consensus(stage2, label_to_model, agg)
        assert result["score"] >= 90
        assert result["winner_model"] == "m-a"
        assert result["total_voters"] == 3

    def test_contested_consensus_low_score(self):
        label_to_model = {
            "Response A": "m-a",
            "Response B": "m-b",
            "Response C": "m-c",
        }
        stage2 = self._make_stage2([
            "FINAL RANKING:\n1. Response A\n2. Response B\n3. Response C",
            "FINAL RANKING:\n1. Response B\n2. Response C\n3. Response A",
            "FINAL RANKING:\n1. Response C\n2. Response A\n3. Response B",
        ])
        agg = self.calc_agg(stage2, label_to_model)
        result = self.calc_consensus(stage2, label_to_model, agg)
        assert result["score"] < 60

    def test_result_keys_present(self):
        label_to_model = {"Response A": "m-a"}
        stage2 = self._make_stage2(["FINAL RANKING:\n1. Response A"])
        agg = self.calc_agg(stage2, label_to_model)
        result = self.calc_consensus(stage2, label_to_model, agg)
        expected_keys = {
            "score", "tier", "tier_label", "badge_icon",
            "kendall_w", "top_pick_agreement_pct", "total_voters",
            "winner_model", "winner_first_places", "summary", "vote_matrix"
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_score_bounded_0_to_100(self):
        label_to_model = {"Response A": "m-a", "Response B": "m-b"}
        stage2 = self._make_stage2(
            ["FINAL RANKING:\n1. Response A\n2. Response B"]
        )
        agg = self.calc_agg(stage2, label_to_model)
        result = self.calc_consensus(stage2, label_to_model, agg)
        assert 0 <= result["score"] <= 100


# ===========================================================================
# 4. get_persona
# ===========================================================================
class TestGetPersona:
    def setup_method(self):
        (self.parse, self.calc_agg, self.calc_consensus,
         self.get_persona, self.personas) = _import_council()

    def test_valid_persona_ids(self):
        for pid in self.personas.keys():
            p = self.get_persona(pid)
            assert p["id"] == pid

    def test_invalid_persona_falls_back_to_strict_truth(self):
        p = self.get_persona("nonexistent_persona")
        assert p["id"] == "strict_truth"

    def test_none_persona_falls_back_to_strict_truth(self):
        p = self.get_persona(None)
        assert p["id"] == "strict_truth"

    def test_all_personas_have_required_keys(self):
        required = {
            "id", "name", "icon", "badge", "description",
            "system_stage1", "stage2_criteria", "stage3_system"
        }
        for pid, persona in self.personas.items():
            missing = required - set(persona.keys())
            assert not missing, f"Persona '{pid}' missing keys: {missing}"

    def test_persona_system_stage1_nonempty(self):
        for pid, persona in self.personas.items():
            assert persona["system_stage1"].strip(), \
                f"Persona '{pid}' has empty system_stage1"

    def test_persona_stage3_system_nonempty(self):
        for pid, persona in self.personas.items():
            assert persona["stage3_system"].strip(), \
                f"Persona '{pid}' has empty stage3_system"


# ===========================================================================
# 5. Storage module (isolated to a temp directory)
# ===========================================================================
class TestStorage:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conv_dir = os.path.join(self.tmpdir, "conversations")
        os.makedirs(self.conv_dir, exist_ok=True)

        import backend.storage as storage_mod
        self._storage = storage_mod
        self._orig_data_dir = storage_mod.DATA_DIR
        storage_mod.DATA_DIR = self.conv_dir

    def teardown_method(self):
        import backend.storage as storage_mod
        storage_mod.DATA_DIR = self._orig_data_dir
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_and_get_conversation(self):
        conv = self._storage.create_conversation("conv-001")
        assert conv["id"] == "conv-001"
        assert conv["messages"] == []

        retrieved = self._storage.get_conversation("conv-001")
        assert retrieved is not None
        assert retrieved["id"] == "conv-001"

    def test_get_nonexistent_returns_none(self):
        assert self._storage.get_conversation("ghost") is None

    def test_add_user_message(self):
        self._storage.create_conversation("conv-002")
        self._storage.add_user_message("conv-002", "Hello!")
        conv = self._storage.get_conversation("conv-002")
        assert len(conv["messages"]) == 1
        assert conv["messages"][0]["role"] == "user"
        assert conv["messages"][0]["content"] == "Hello!"

    def test_add_assistant_message(self):
        self._storage.create_conversation("conv-003")
        self._storage.add_user_message("conv-003", "Question?")
        self._storage.add_assistant_message(
            "conv-003",
            stage1=[{"model": "m-a", "response": "S1"}],
            stage2=[{"model": "m-a", "ranking": "FINAL RANKING:\n1. Response A"}],
            stage3={"model": "chairman", "response": "Final"},
            metadata={"consensus": {"score": 90}}
        )
        conv = self._storage.get_conversation("conv-003")
        assert len(conv["messages"]) == 2
        asst = conv["messages"][1]
        assert asst["role"] == "assistant"
        assert "stage1" in asst
        assert "stage3" in asst

    def test_update_title(self):
        self._storage.create_conversation("conv-004")
        self._storage.update_conversation_title("conv-004", "My Title")
        conv = self._storage.get_conversation("conv-004")
        assert conv["title"] == "My Title"

    def test_delete_conversation(self):
        self._storage.create_conversation("conv-005")
        assert self._storage.delete_conversation("conv-005") is True
        assert self._storage.get_conversation("conv-005") is None

    def test_delete_nonexistent_returns_false(self):
        assert self._storage.delete_conversation("ghost-conv") is False

    def test_list_conversations_sorted_newest_first(self):
        import time
        for cid in ["conv-aa", "conv-bb", "conv-cc"]:
            self._storage.create_conversation(cid)
            time.sleep(0.02)
        listed = self._storage.list_conversations()
        assert listed[0]["id"] == "conv-cc"
        assert listed[-1]["id"] == "conv-aa"

    def test_list_conversations_metadata_only(self):
        self._storage.create_conversation("conv-006")
        self._storage.add_user_message("conv-006", "Hi")
        listed = self._storage.list_conversations()
        meta = next(c for c in listed if c["id"] == "conv-006")
        assert "messages" not in meta
        assert meta["message_count"] == 1

    def test_add_user_message_to_missing_conv_raises(self):
        with pytest.raises(ValueError, match="not found"):
            self._storage.add_user_message("nonexistent-xyz", "msg")


# ===========================================================================
# 6. Config sanity checks
# ===========================================================================
class TestConfig:
    def test_council_models_nonempty(self):
        from backend.config import COUNCIL_MODELS
        assert len(COUNCIL_MODELS) > 0

    def test_chairman_model_format(self):
        from backend.config import CHAIRMAN_MODEL
        assert isinstance(CHAIRMAN_MODEL, str)
        assert "/" in CHAIRMAN_MODEL, "Should be 'provider/model' format"

    def test_openrouter_url_starts_with_https(self):
        from backend.config import OPENROUTER_API_URL
        assert OPENROUTER_API_URL.startswith("https://")

    def test_all_council_models_are_provider_slash_model(self):
        from backend.config import COUNCIL_MODELS
        for m in COUNCIL_MODELS:
            assert isinstance(m, str)
            assert "/" in m, f"Model '{m}' should be 'provider/model' format"


# ===========================================================================
# 7. FastAPI routes smoke tests (no real network calls)
# ===========================================================================
class TestFastAPIRoutes:
    def setup_method(self):
        try:
            from fastapi.testclient import TestClient
            import backend.storage as storage_mod

            self.tmpdir = tempfile.mkdtemp()
            self.conv_dir = os.path.join(self.tmpdir, "conversations")
            os.makedirs(self.conv_dir, exist_ok=True)
            self._orig_data_dir = storage_mod.DATA_DIR
            storage_mod.DATA_DIR = self.conv_dir

            from backend.main import app
            self.client = TestClient(app)
            self.available = True
        except Exception:
            self.available = False

    def teardown_method(self):
        if self.available:
            import backend.storage as storage_mod
            storage_mod.DATA_DIR = self._orig_data_dir
            import shutil
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _skip_if_unavailable(self):
        if not self.available:
            pytest.skip("FastAPI TestClient not available")

    def test_health_check(self):
        self._skip_if_unavailable()
        r = self.client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_conversations_empty(self):
        self._skip_if_unavailable()
        r = self.client.get("/api/conversations")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_conversation(self):
        self._skip_if_unavailable()
        r = self.client.post("/api/conversations", json={})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["title"] == "New Conversation"
        assert data["messages"] == []

    def test_get_nonexistent_conversation_404(self):
        self._skip_if_unavailable()
        r = self.client.get("/api/conversations/nonexistent-id")
        assert r.status_code == 404

    def test_delete_nonexistent_conversation_404(self):
        self._skip_if_unavailable()
        r = self.client.delete("/api/conversations/nonexistent-id")
        assert r.status_code == 404

    def test_list_models_returns_curated_list(self):
        self._skip_if_unavailable()
        r = self.client.get("/api/models")
        assert r.status_code == 200
        models = r.json()
        assert len(models) > 0
        for m in models:
            assert "id" in m and "name" in m and "provider" in m

    def test_list_personas_returns_all_personas(self):
        self._skip_if_unavailable()
        r = self.client.get("/api/personas")
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert "strict_truth" in ids
        assert "cybersecurity" in ids

    def test_update_settings_valid(self):
        self._skip_if_unavailable()
        payload = {
            "council_models": ["openai/gpt-4o", "anthropic/claude-3.7-sonnet"],
            "chairman_model": "openai/gpt-4o",
            "persona": "code_architect"
        }
        r = self.client.post("/api/settings", json=payload)
        assert r.status_code == 200
        assert "openai/gpt-4o" in r.json()["council_models"]

    def test_update_settings_empty_council_returns_400(self):
        self._skip_if_unavailable()
        payload = {
            "council_models": [],
            "chairman_model": "openai/gpt-4o",
            "persona": "strict_truth"
        }
        r = self.client.post("/api/settings", json=payload)
        assert r.status_code == 400

    def test_create_then_delete_conversation(self):
        self._skip_if_unavailable()
        create_r = self.client.post("/api/conversations", json={})
        assert create_r.status_code == 200
        conv_id = create_r.json()["id"]

        del_r = self.client.delete(f"/api/conversations/{conv_id}")
        assert del_r.status_code == 204

        get_r = self.client.get(f"/api/conversations/{conv_id}")
        assert get_r.status_code == 404
