"""Knowledge Intake Engine — extensible source ingestion.

Developer map: docs/KNOWLEDGE_INTAKE_ENGINE.md

Pipeline: Source → Normalizer → Parser → Chunker → Embedding → Memory → Reasoning → Vector
Phase 1 (PDF): stops after Parser → prompt inject. Embedding slot reserved, not implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

IntakeSourceKind = Literal[
    "attachment",
    "url",
    "github",
    "youtube",
    "notion",
    "figma",
    "google_docs",
    "spreadsheet",
]

IntakeStatus = Literal["stored_only", "parsed", "unsupported", "denied"]


class PipelineStage(str, Enum):
    """Canonical stages — implement incrementally; EMBED is a no-op until RAG phase."""

    SOURCE = "source"
    NORMALIZE = "normalize"
    PARSE = "parse"
    CHUNK = "chunk"
    EMBED = "embed"
    MEMORY = "memory"
    REASON = "reason"
    VECTOR = "vector"


@dataclass(frozen=True)
class KnowledgeChunk:
    """Chunker output — one retrievable unit (prompt inject or future embedding)."""

    index: int
    text: str
    token_estimate: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntakePipelineState:
    """Carries artifacts through the pipeline for one intake job."""

    descriptor: "IntakeDescriptor"
    stage: PipelineStage = PipelineStage.SOURCE
    normalized_mime: str = ""
    parsed_text: str = ""
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    embedding_ref: str | None = None  # future: id in vector store
    memory_path: Path | None = None
    context_block: str = ""
    error: str = ""

    def advance(self, stage: PipelineStage) -> None:
        self.stage = stage


@dataclass(frozen=True)
class IntakeDescriptor:
    """What to ingest — attachment today; other kinds add fields later."""

    kind: IntakeSourceKind
    attachment_id: str | None = None
    content_type: str | None = None
    path: Path | None = None
    url: str | None = None
    label: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntakeResult:
    status: IntakeStatus
    kind: IntakeSourceKind
    text_excerpt: str = ""
    page_count: int = 0
    pages_included: int = 0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_context_block(self) -> str:
        if self.status != "parsed" or not self.text_excerpt:
            return ""
        label = self.metadata.get("filename") or self.kind
        return f"[Документ: {label}]\n{self.text_excerpt}"


@runtime_checkable
class IntakeSource(Protocol):
    kind: IntakeSourceKind

    def can_handle(self, descriptor: IntakeDescriptor) -> bool: ...

    def ingest(
        self,
        descriptor: IntakeDescriptor,
        *,
        memory_dir: Path | None = None,
        tier: str = "free",
    ) -> IntakeResult: ...


class KnowledgeIntakeRegistry:
    """Register intake sources — PDF module added in AI-1 slice."""

    def __init__(self) -> None:
        self._sources: list[IntakeSource] = []

    def register(self, source: IntakeSource) -> None:
        self._sources.append(source)

    def resolve(self, descriptor: IntakeDescriptor) -> IntakeSource | None:
        for src in self._sources:
            if src.can_handle(descriptor):
                return src
        return None

    def ingest(self, descriptor: IntakeDescriptor, **kwargs: Any) -> IntakeResult:
        src = self.resolve(descriptor)
        if not src:
            return IntakeResult(
                status="unsupported",
                kind=descriptor.kind,
                reason="no intake source registered for descriptor",
            )
        return src.ingest(descriptor, **kwargs)

    def run_pipeline(
        self,
        descriptor: IntakeDescriptor,
        *,
        through: PipelineStage = PipelineStage.PARSE,
        **kwargs: Any,
    ) -> IntakePipelineState:
        """Execute pipeline stages up to ``through``. EMBED/MEMORY are stubs."""
        state = IntakePipelineState(descriptor=descriptor)
        state.advance(PipelineStage.SOURCE)
        result = self.ingest(descriptor, **kwargs)
        if result.status == "denied":
            state.error = result.reason
            return state
        state.advance(PipelineStage.NORMALIZE)
        state.normalized_mime = descriptor.content_type or ""
        if result.status != "parsed":
            state.error = result.reason or result.status
            return state
        state.advance(PipelineStage.PARSE)
        state.parsed_text = result.text_excerpt
        state.context_block = result.to_context_block()
        if through.value in (PipelineStage.CHUNK.value, PipelineStage.EMBED.value):
            state.advance(PipelineStage.CHUNK)
            state.chunks = _default_chunk(result.text_excerpt)
        if through == PipelineStage.EMBED:
            state.advance(PipelineStage.EMBED)
            state.embedding_ref = None  # reserved — vector index not implemented
        return state

    def list_kinds(self) -> list[str]:
        return sorted({s.kind for s in self._sources})


def _default_chunk(text: str, *, max_chars: int = 4000) -> list[KnowledgeChunk]:
    """Minimal chunker — single chunk until RAG phase."""
    t = (text or "").strip()
    if not t:
        return []
    if len(t) <= max_chars:
        return [KnowledgeChunk(index=0, text=t, token_estimate=len(t) // 4)]
    return [
        KnowledgeChunk(index=0, text=t[:max_chars], token_estimate=max_chars // 4),
    ]
