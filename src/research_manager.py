from dotenv import load_dotenv
import os
from agents import Runner, trace, gen_trace_id
from research_agents.search_agent import search_agent
from research_agents.planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from research_agents.writer_agent import writer_agent, ReportData
from research_agents.email_agent import email_agent
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep search process, yielding the status updates and the final report """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"Starting research..."
            search_plan=await self.plan_searches(query)
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."
            search_results = await self.perform_searches(search_plan)
            yield f"Searches completed. Generating report..."
            report = await self.write_report(query, search_results)
            yield f"Report generated. Rendering it..."
            await self.send_email(report)
            yield "Research complete"
            yield report.markdown_report

    async def search(self, item: WebSearchItem) -> str | None :
        """ perform a search for a query """
        input_message = f"Search term: {item.query}\nReason for searching: {item.reason}"
        result = await Runner.run(search_agent, input_message)
        return result.final_output

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        tasks = [self.search(item) for item in search_plan.searches]
        return await asyncio.gather(*tasks)

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write a report for teh query """
        input_message = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input_message)
        return result.final_output
                
    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)
