"""Decision Log – persistent record of portfolio meeting outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from core.models import (
    AgentReport,
    AgentUtterance,
    MeetingPhase,
    MeetingRecord,
    PortfolioDecision,
)


class DecisionLog:
    """Append-only log of :class:`MeetingRecord` entries.

    Writes both JSON (machine-readable) and Markdown (human-readable)
    for every recorded meeting.

    Args:
        log_dir: Directory where decision files are stored.
                 Defaults to ``<project>/logs/decisions``.
    """

    def __init__(self, log_dir: str | Path | None = None) -> None:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs" / "decisions"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.log_dir / "index.json"
        self._entries: list[dict[str, Any]] = self._load_index()

    def record(self, meeting_record: MeetingRecord) -> tuple[Path, Path]:
        """Persist a meeting record as JSON and Markdown.

        Args:
            meeting_record: Complete meeting transcript and decision.

        Returns:
            Tuple of (json_path, markdown_path).
        """
        timestamp = meeting_record.recorded_at.strftime("%Y%m%d_%H%M%S")
        base_name = f"{meeting_record.meeting_date.isoformat()}_{timestamp}"
        json_path = self.log_dir / f"{base_name}.json"
        md_path = self.log_dir / f"{base_name}.md"

        payload = self._serialize_meeting_record(meeting_record)
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        md_path.write_text(
            self.export_markdown(meeting_record),
            encoding="utf-8",
        )

        index_entry = {
            "meeting_id": meeting_record.meeting_id,
            "json_file": json_path.name,
            "md_file": md_path.name,
            "meeting_date": meeting_record.meeting_date.isoformat(),
            "summary": meeting_record.meeting_summary,
            "trade_count": len(meeting_record.decision.trades),
            "approved": meeting_record.decision.approved,
            "recorded_at": meeting_record.recorded_at.isoformat(),
        }
        self._entries.append(index_entry)
        self._save_index()

        return json_path, md_path

    def export_markdown(self, meeting_record: MeetingRecord) -> str:
        """Render a meeting record as a human-readable Markdown transcript."""
        lines = [
            f"# Weekly Meeting — {meeting_record.meeting_date.isoformat()}",
            "",
            "## Participants",
            ", ".join(meeting_record.participants),
            "",
            "## Meeting Summary",
            meeting_record.meeting_summary,
            "",
            "## Transcript",
            "",
        ]

        phase_headers = {
            MeetingPhase.OPENING: "### Opening",
            MeetingPhase.REPORT: "### Reports",
            MeetingPhase.DELIBERATION: "### Deliberation",
            MeetingPhase.DECISION: "### Decision",
        }

        current_phase: MeetingPhase | None = None
        for utterance in meeting_record.utterances:
            if utterance.phase != current_phase:
                current_phase = utterance.phase
                header = phase_headers.get(current_phase, f"### {current_phase.value}")
                lines.append(header)
                lines.append("")

            lines.append(f"**{utterance.agent_name}:**")
            lines.append(utterance.content)
            lines.append("")

        lines.extend([
            "## Final Decision",
            meeting_record.decision.summary,
            "",
        ])

        if meeting_record.decision.trades:
            lines.append("### Proposed Trades")
            lines.append("")
            for trade in meeting_record.decision.trades:
                lines.append(
                    f"- **{trade.action.upper()} {trade.ticker}** "
                    f"({trade.shares} shares): {trade.rationale}"
                )
            lines.append("")
        else:
            lines.append("*No trades proposed — maintain current allocation.*")
            lines.append("")

        approval_label = (
            "Approved"
            if meeting_record.decision.approved
            else "Pending human review"
        )
        lines.extend([
            "## Approval",
            f"**Status:** {approval_label}",
            f"**Decision source:** {meeting_record.decision.decision_source}",
            "",
            "## Reasoning",
            "",
        ])
        for reason in meeting_record.decision.reasoning:
            lines.append(f"- {reason}")

        return "\n".join(lines)

    def get_by_date(self, meeting_date: date) -> list[dict[str, Any]]:
        """Return all meeting records for a given date."""
        target = meeting_date.isoformat()
        results: list[dict[str, Any]] = []
        for entry in self._entries:
            if entry["meeting_date"] == target:
                results.append(self._load_entry(entry["json_file"]))
        return results

    def get_all(self) -> list[dict[str, Any]]:
        """Return all indexed meetings, newest first."""
        return sorted(
            self._entries,
            key=lambda e: e.get("recorded_at", ""),
            reverse=True,
        )

    def load_meeting(self, filename: str) -> dict[str, Any]:
        """Load a single meeting JSON file by filename."""
        return self._load_entry(filename)

    def update_approval(self, meeting_id: str, approved: bool) -> dict[str, Any] | None:
        """Set approval status on an existing meeting and refresh its log files."""
        for index, entry in enumerate(self._entries):
            if entry.get("meeting_id") != meeting_id:
                continue

            json_path = self.log_dir / entry["json_file"]
            data = json.loads(json_path.read_text(encoding="utf-8"))
            data["decision"]["approved"] = approved
            data["approval_status"] = "approved" if approved else "rejected"
            data["approved_at"] = datetime.utcnow().isoformat()
            json_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            md_path = self.log_dir / entry["md_file"]
            md_path.write_text(
                self._markdown_from_payload(data),
                encoding="utf-8",
            )

            self._entries[index]["approved"] = approved
            self._entries[index]["approval_status"] = (
                "approved" if approved else "rejected"
            )
            self._save_index()
            return data

        return None

    def _markdown_from_payload(self, payload: dict[str, Any]) -> str:
        """Rebuild markdown from a serialized meeting payload."""
        from core.models import (
            AgentReport,
            AgentUtterance,
            MeetingPhase,
            MeetingRecord,
            PortfolioDecision,
            TradeAction,
        )

        utterances = []
        for item in payload.get("utterances", []):
            utterances.append(
                AgentUtterance(
                    agent_name=item["agent_name"],
                    role=item["role"],
                    phase=MeetingPhase(item["phase"]),
                    content=item["content"],
                )
            )

        decision_data = payload["decision"]
        trades = [TradeAction(**trade) for trade in decision_data.get("trades", [])]
        decision = PortfolioDecision(
            meeting_date=date.fromisoformat(decision_data["meeting_date"]),
            trades=trades,
            summary=decision_data["summary"],
            reasoning=decision_data.get("reasoning", []),
            agent_reports=[],
            approved=decision_data.get("approved", False),
            deliberation=decision_data.get("deliberation"),
            decision_source=decision_data.get("decision_source", "rule_based"),
        )

        record = MeetingRecord(
            meeting_id=payload["meeting_id"],
            meeting_date=date.fromisoformat(payload["meeting_date"]),
            participants=payload.get("participants", []),
            utterances=utterances,
            meeting_summary=payload.get("meeting_summary", decision.summary),
            decision=decision,
        )
        return self.export_markdown(record)

    def _load_index(self) -> list[dict[str, Any]]:
        if not self._index_path.exists():
            return []
        return json.loads(self._index_path.read_text(encoding="utf-8"))

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_entry(self, filename: str) -> dict[str, Any]:
        path = self.log_dir / filename
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _serialize_meeting_record(record: MeetingRecord) -> dict[str, Any]:
        """Convert a MeetingRecord to a JSON-serializable dict."""
        return {
            "meeting_id": record.meeting_id,
            "meeting_date": record.meeting_date.isoformat(),
            "participants": record.participants,
            "meeting_summary": record.meeting_summary,
            "recorded_at": record.recorded_at.isoformat(),
            "utterances": [
                DecisionLog._serialize_utterance(u) for u in record.utterances
            ],
            "decision": DecisionLog._serialize_decision(record.decision),
        }

    @staticmethod
    def _serialize_utterance(utterance: AgentUtterance) -> dict[str, Any]:
        data = asdict(utterance)
        data["phase"] = utterance.phase.value
        data["timestamp"] = utterance.timestamp.isoformat()
        return data

    @staticmethod
    def _serialize_decision(decision: PortfolioDecision) -> dict[str, Any]:
        return {
            "meeting_date": decision.meeting_date.isoformat(),
            "summary": decision.summary,
            "reasoning": decision.reasoning,
            "approved": decision.approved,
            "deliberation": decision.deliberation,
            "decision_source": decision.decision_source,
            "decided_at": decision.decided_at.isoformat(),
            "trades": [asdict(t) for t in decision.trades],
            "agent_reports": [
                DecisionLog._serialize_report(r) for r in decision.agent_reports
            ],
        }

    @staticmethod
    def _serialize_report(report: AgentReport) -> dict[str, Any]:
        data = asdict(report)
        data["generated_at"] = report.generated_at.isoformat()
        for score in data.get("stock_scores", []):
            if "recommendation" in score:
                score["recommendation"] = (
                    score["recommendation"].value
                    if hasattr(score["recommendation"], "value")
                    else str(score["recommendation"])
                )
        return data