"""Integration and unit tests for the Conversational Math Mayhem Director Agent (Phase 5.5)."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.director_adapter import (
    ConversationalIntent,
    DirectorProductionAdapter,
    IntentResult,
)
from app.director_memory import (
    DirectorEpisodeContext,
    DirectorMemoryEngine,
    DirectorRevisionSnapshot,
    DirectorSession,
    ProjectMemoryRegistry,
)


@pytest.fixture
def memory_engine(tmp_path):
    """Isolated SQLite database for director memory testing."""
    db_file = tmp_path / "test_director.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    mem = DirectorMemoryEngine(session_factory=session_factory)
    return mem


@pytest.fixture
def adapter(memory_engine):
    """DirectorProductionAdapter connected to isolated test memory."""
    return DirectorProductionAdapter(memory_engine=memory_engine)


def test_intent_parsing_coverage(adapter):
    """Verify natural language classification across all required conversational intents."""
    # 1. Idea Brainstorming
    res = adapter.parse_intent("Give me three funny ideas about imaginary numbers.")
    assert res.intent == ConversationalIntent.IDEA_BRAINSTORM
    assert "imaginary" in res.extracted_topic

    # 2. Start Episode
    res = adapter.parse_intent("Let's start working on Episode 002.")
    assert res.intent == ConversationalIntent.START_EPISODE
    assert res.target_episode == "EP002"

    # 3. Produce Preview
    res = adapter.parse_intent("Go ahead and produce a preview.")
    assert res.intent == ConversationalIntent.PRODUCE_PREVIEW

    # 4. Revision Request
    res = adapter.parse_intent("The character's reaction is too quick. Give him another second to look confused.")
    assert res.intent == ConversationalIntent.REVISION_REQUEST

    # 5. Rollback
    res = adapter.parse_intent("Undo the last revision.")
    assert res.intent == ConversationalIntent.ROLLBACK_REQUEST

    # 6. Status Query
    res = adapter.parse_intent("How far along is the episode?")
    assert res.intent == ConversationalIntent.STATUS_QUERY

    # 7. Approve Master
    res = adapter.parse_intent("This looks great, let's lock it in as the official master.")
    assert res.intent == ConversationalIntent.APPROVE_MASTER


def test_brainstorm_ideas_mathematical_rigor(adapter):
    """Verify that brainstormed concepts maintain SymPy rigor and include cartoon disclaimers."""
    ideas = adapter.brainstorm_ideas("imaginary numbers")
    assert len(ideas) >= 3
    for idea in ideas:
        assert "title" in idea
        assert "math_truth" in idea
        assert "fictional_metaphor" in idea
        assert idea["disclaimer_required"] is True
        assert "disclaimer_text" in idea
        assert len(idea["disclaimer_text"]) > 10


def test_episode_initialization_and_memory_persistence(adapter, memory_engine):
    """Verify that starting an episode saves state to SQLite and session context."""
    ctx = adapter.start_episode(episode_code="EP002")
    assert ctx["episode_code"] == "EP002"
    assert ctx["status"] == "DRAFT"
    assert ctx["current_version"] == 1
    assert ctx["math_verified"] is True
    assert "scene_parameters" in ctx

    # Check persistence in database
    retrieved = memory_engine.get_episode_context("EP002")
    assert retrieved is not None
    assert retrieved["title"] == ctx["title"]
    assert retrieved["scene_parameters"]["equation_title"] == "COMPLEX ROTATION : i = √-1"

    # Check active session updated
    sess = memory_engine.get_or_create_session()
    assert sess["active_episode_code"] == "EP002"
    assert sess["active_version_number"] == 1


def test_conversational_revision_targeting_and_preservation(adapter, tmp_path):
    """Verify that applying a revision targets only the relevant parameters and preserves unaffected ones."""
    adapter.start_episode(episode_code="EP002")
    initial_ctx = adapter.memory.get_episode_context("EP002")
    initial_walk_dur = initial_ctx["scene_parameters"]["walk_in_duration_sec"]
    initial_reaction_dur = initial_ctx["scene_parameters"]["reaction_duration_sec"]

    # Apply revision: "Make the reaction slower, give him another second to look confused"
    rev_res = adapter.apply_revision(
        episode_code="EP002",
        user_instruction="Make the reaction slower, give him another second to look confused",
        output_dir=tmp_path,
    )

    assert rev_res["success"] is True
    assert rev_res["version"] == 2
    assert 4 in rev_res["targeted_scenes"]  # Scene 4: reaction
    assert rev_res["parameter_deltas"]["reaction_duration_sec"] > initial_reaction_dur
    assert rev_res["parameter_deltas"]["reaction_emotion"] == "CONFUSION"

    # Verify unaffected parameters remained strictly preserved
    updated_ctx = adapter.memory.get_episode_context("EP002")
    assert updated_ctx["scene_parameters"]["walk_in_duration_sec"] == initial_walk_dur
    assert updated_ctx["status"] == "PREVIEW_READY"


def test_revision_rollback_functionality(adapter, tmp_path):
    """Verify that rollback restores the previous parameter snapshot and decrements version."""
    adapter.start_episode(episode_code="EP002")
    adapter.apply_revision(
        episode_code="EP002",
        user_instruction="Make the reaction slower",
        output_dir=tmp_path,
    )

    ctx_v2 = adapter.memory.get_episode_context("EP002")
    assert ctx_v2["current_version"] == 2

    # Execute rollback
    rollback_res = adapter.rollback(episode_code="EP002")
    assert rollback_res["success"] is True
    assert rollback_res["restored_version"] == 1

    ctx_restored = adapter.memory.get_episode_context("EP002")
    assert ctx_restored["current_version"] == 1


def test_master_approval_and_immutability(adapter):
    """Verify locking an episode version as an approved master."""
    adapter.start_episode(episode_code="EP002")
    appr = adapter.approve_master(episode_code="EP002", approved_by="owner_primary")
    assert appr["success"] is True
    assert appr["status"] == "APPROVED"
    assert appr["approved_by"] == "owner_primary"

    # Check status via adapter
    status = adapter.get_status("EP002")
    assert status["status"] == "APPROVED"


def test_conversational_turn_end_to_end(adapter, tmp_path):
    """Verify end-to-end dispatch of user messages into natural responses and artifact links."""
    # Turn 1: Brainstorm
    turn1 = adapter.handle_conversational_turn("Give me three funny ideas about imaginary numbers")
    assert turn1["intent"] == "IDEA_BRAINSTORM"
    assert "Idea 1:" in turn1["response_text"]
    assert len(turn1["artifacts"]["ideas"]) >= 3

    # Turn 2: Start episode
    turn2 = adapter.handle_conversational_turn("Let's start working on Episode 002")
    assert turn2["intent"] == "START_EPISODE"
    assert "EP002" in turn2["response_text"]

    # Turn 3: Status query
    turn3 = adapter.handle_conversational_turn("How far along is the episode?")
    assert turn3["intent"] == "STATUS_QUERY"
    assert "EP002" in turn3["response_text"]
