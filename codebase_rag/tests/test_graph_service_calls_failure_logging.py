from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from codebase_rag.services.graph_service import MemgraphIngestor


@pytest.fixture
def graph_service() -> MemgraphIngestor:
    """Create a MemgraphIngestor instance with mocked database."""
    ingestor = MemgraphIngestor(host="localhost", port=7687, batch_size=100)
    ingestor.conn = MagicMock()
    return ingestor


@pytest.fixture
def log_messages() -> Generator[list[str], None, None]:
    """Capture log messages using a custom sink."""
    messages: list[str] = []

    def sink(message: Any) -> None:
        messages.append(str(message))

    handler_id = logger.add(sink, format="{message}")
    yield messages
    logger.remove(handler_id)


def test_calls_deferred_not_in_relationship_buffer(
    graph_service: MemgraphIngestor,
) -> None:
    """CALLS relationships should go to deferred buffer, not relationship_buffer."""
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassB.methodB()"),
    )
    graph_service.ensure_relationship_batch(
        ("Module", "qualified_name", "project.moduleA"),
        "IMPORTS",
        ("Module", "qualified_name", "project.moduleB"),
    )

    assert len(graph_service.deferred_calls_buffer) == 1
    assert len(graph_service.relationship_buffer) == 1


def test_calls_not_flushed_during_incremental_flush(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """CALLS should NOT be flushed when relationship buffer triggers incremental flush.

    This is the core fix: previously CALLS relationships were flushed during
    incremental flush when callee nodes might not exist yet in the DB.
    """
    graph_service.batch_size = 3
    for i in range(3):
        graph_service.ensure_relationship_batch(
            ("Module", "qualified_name", f"project.moduleA{i}"),
            "IMPORTS",
            ("Module", "qualified_name", f"project.moduleB{i}"),
        )

    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassB.methodB()"),
    )

    assert len(graph_service.deferred_calls_buffer) == 1
    assert len(graph_service.relationship_buffer) == 0


def test_calls_flushed_on_flush_all(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """Deferred CALLS should be flushed during flush_all()."""
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassB.methodB()"),
    )
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassC.methodC()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassD.methodD()"),
    )

    assert len(graph_service.deferred_calls_buffer) == 2

    with patch.object(
        graph_service,
        "_execute_batch_with_return",
        return_value=[{"created": 2}],
    ):
        graph_service.flush_all()

    assert len(graph_service.deferred_calls_buffer) == 0

    log_text = "\n".join(log_messages)
    assert "Flushing 2 deferred CALLS relationships" in log_text


def test_calls_failure_logging_on_flush_all(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """Test that CALLS failures are logged correctly when flushed via flush_all().

    This validates that the failure count is calculated correctly using
    batch-specific counts, not cumulative totals.
    """
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassB.methodB()"),
    )
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.NonExistent.missing()"),
    )
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassC.methodC()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.AlsoMissing.gone()"),
    )

    with patch.object(
        graph_service,
        "_execute_batch_with_return",
        return_value=[{"created": 1}],
    ):
        graph_service.flush_all()

    log_text = "\n".join(log_messages)
    assert "Failed to create 2 CALLS relationships" in log_text
    assert "nodes may not exist" in log_text


def test_calls_success_no_failure_logging(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """Test that successful CALLS don't trigger failure warnings."""
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassA.methodA()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassB.methodB()"),
    )
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.module.ClassC.methodC()"),
        "CALLS",
        ("Method", "qualified_name", "project.module.ClassD.methodD()"),
    )

    with patch.object(
        graph_service,
        "_execute_batch_with_return",
        return_value=[{"created": 2}],
    ):
        graph_service.flush_all()

    log_text = "\n".join(log_messages)
    assert "Failed to create" not in log_text
    assert "nodes may not exist" not in log_text


def test_non_calls_relationships_no_failure_logging(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """Test that failures in non-CALLS relationships don't trigger CALLS-specific logging."""
    graph_service.ensure_relationship_batch(
        ("Module", "qualified_name", "project.moduleA"),
        "IMPORTS",
        ("Module", "qualified_name", "project.moduleB"),
    )
    graph_service.ensure_relationship_batch(
        ("Module", "qualified_name", "project.moduleA"),
        "IMPORTS",
        ("Module", "qualified_name", "project.missing"),
    )

    with patch.object(
        graph_service,
        "_execute_batch_with_return",
        return_value=[{"created": 1}, {"created": 0}],
    ):
        graph_service.flush_relationships()

    log_text = "\n".join(log_messages)
    assert "Failed to create" not in log_text or "CALLS" not in log_text


def test_deferred_calls_empty_no_log(
    graph_service: MemgraphIngestor, log_messages: list[str]
) -> None:
    """When no CALLS in deferred buffer, _flush_deferred_calls should be silent."""
    with patch.object(
        graph_service,
        "_execute_batch_with_return",
        return_value=[],
    ):
        graph_service.flush_all()

    log_text = "\n".join(log_messages)
    assert "deferred CALLS" not in log_text


def test_mixed_relationships_separation(
    graph_service: MemgraphIngestor,
) -> None:
    """CALLS and non-CALLS should be cleanly separated into different buffers."""
    graph_service.ensure_relationship_batch(
        ("Module", "qualified_name", "project.moduleA"),
        "IMPORTS",
        ("Module", "qualified_name", "project.moduleB"),
    )
    graph_service.ensure_relationship_batch(
        ("Method", "qualified_name", "project.ClassA.methodA"),
        "CALLS",
        ("Method", "qualified_name", "project.ClassB.methodB"),
    )
    graph_service.ensure_relationship_batch(
        ("Class", "qualified_name", "project.ClassC"),
        "INHERITS",
        ("Class", "qualified_name", "project.ClassD"),
    )
    graph_service.ensure_relationship_batch(
        ("Function", "qualified_name", "project.funcA"),
        "CALLS",
        ("Function", "qualified_name", "project.funcB"),
    )

    assert len(graph_service.relationship_buffer) == 2
    assert len(graph_service.deferred_calls_buffer) == 2

    rel_types = {r[1] for r in graph_service.relationship_buffer}
    deferred_types = {r[1] for r in graph_service.deferred_calls_buffer}
    assert "CALLS" not in rel_types
    assert deferred_types == {"CALLS"}
