import unittest
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from research_agents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from research_agents.writer_agent import ReportData, writer_agent
from research_manager import ResearchManager, email_agent, search_agent


class ResearchManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_runs_agent_with_query_and_reason(self):
        result = SimpleNamespace(final_output="Search summary")

        with patch("research_manager.Runner.run", new=AsyncMock(return_value=result)) as run:
            summary = await ResearchManager().search(
                WebSearchItem(query="climate policy", reason="Find current policy")
            )

        self.assertEqual(summary, "Search summary")
        run.assert_awaited_once_with(
            search_agent,
            "Search term: climate policy\nReason for searching: Find current policy",
        )

    async def test_plan_searches_runs_planner_agent(self):
        plan = WebSearchPlan(searches=[])
        result = SimpleNamespace(final_output=plan)

        with patch("research_manager.Runner.run", new=AsyncMock(return_value=result)) as run:
            actual_plan = await ResearchManager().plan_searches("climate policy")

        self.assertIs(actual_plan, plan)
        run.assert_awaited_once_with(planner_agent, "Query: climate policy")

    async def test_perform_searches_returns_summaries_in_plan_order(self):
        manager = ResearchManager()
        first = WebSearchItem(query="first", reason="First")
        second = WebSearchItem(query="second", reason="Second")
        manager.search = AsyncMock(side_effect=["first summary", "second summary"])

        summaries = await manager.perform_searches(WebSearchPlan(searches=[first, second]))

        self.assertEqual(summaries, ["first summary", "second summary"])
        self.assertEqual(
            manager.search.await_args_list,
            [unittest.mock.call(first), unittest.mock.call(second)],
        )

    async def test_write_report_runs_writer_agent_with_query_and_results(self):
        report = ReportData(
            short_summary="Summary",
            markdown_report="# Report",
            follow_up_questions=[],
        )
        result = SimpleNamespace(final_output=report)

        with patch("research_manager.Runner.run", new=AsyncMock(return_value=result)) as run:
            actual_report = await ResearchManager().write_report(
                "climate policy", ["Finding one", "Finding two"]
            )

        self.assertIs(actual_report, report)
        run.assert_awaited_once_with(
            writer_agent,
            "Original query: climate policy\n"
            "Summarized search results: ['Finding one', 'Finding two']",
        )

    async def test_send_email_runs_email_agent_with_report(self):
        report = ReportData(
            short_summary="Summary",
            markdown_report="# Report",
            follow_up_questions=[],
        )

        with patch("research_manager.Runner.run", new=AsyncMock()) as run:
            await ResearchManager().send_email(report)

        run.assert_awaited_once_with(email_agent, "# Report")

    async def test_run_yields_progress_and_final_report(self):
        report = ReportData(
            short_summary="Summary",
            markdown_report="# Final report",
            follow_up_questions=[],
        )
        manager = ResearchManager()
        manager.plan_searches = AsyncMock(return_value=WebSearchPlan(searches=[]))
        manager.perform_searches = AsyncMock(return_value=["Finding"])
        manager.write_report = AsyncMock(return_value=report)
        manager.send_email = AsyncMock()

        with (
            patch("research_manager.gen_trace_id", return_value="trace-id"),
            patch("research_manager.trace", return_value=nullcontext()),
        ):
            updates = [update async for update in manager.run("climate policy")]

        self.assertEqual(
            updates,
            [
                "Starting research...",
                "Searches planned, starting 0 searches...",
                "Searches completed. Generating report...",
                "Report generated. Sending report...",
                "Report sent, research complete",
                "# Final report",
            ],
        )
        manager.plan_searches.assert_awaited_once_with("climate policy")
        manager.perform_searches.assert_awaited_once()
        manager.write_report.assert_awaited_once_with("climate policy", ["Finding"])
        manager.send_email.assert_awaited_once_with(report)


if __name__ == "__main__":
    unittest.main()
