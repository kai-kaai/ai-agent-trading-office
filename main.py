"""Entry point for the AI Agent Trading Office."""

from __future__ import annotations

from core.orchestrator import TradingOfficeOrchestrator, create_sample_context


def main() -> None:
    """Run a sample weekly meeting and print the results."""
    orchestrator = TradingOfficeOrchestrator()
    result = orchestrator.run_weekly_meeting(create_sample_context())

    print("=" * 60)
    print("AI Agent Trading Office – Weekly Meeting")
    print("=" * 60)
    print(f"Participants: {', '.join(result.participants)}")
    print(f"Duration: {result.duration_ms:.1f} ms")
    print(f"\nDecision: {result.decision.summary}")
    print(f"JSON log: {result.json_log_path}")
    print(f"Markdown log: {result.md_log_path}")

    print("\n--- Transcript ---")
    for utterance in result.meeting_record.utterances:
        print(f"\n[{utterance.phase.value}] {utterance.agent_name}:")
        print(utterance.content)

    print("\n--- Reasoning ---")
    for line in result.decision.reasoning:
        print(f"  {line}")


if __name__ == "__main__":
    main()