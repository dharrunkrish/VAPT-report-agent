from crewai import Agent

from config.prompts import EXEC_SUMMARY_BACKSTORY, EXEC_SUMMARY_GOAL
from utils.llm import get_llm


def make_exec_summary_agent(llm=None) -> Agent:
    return Agent(
        role="Executive Summary Analyst",
        goal=EXEC_SUMMARY_GOAL,
        backstory=EXEC_SUMMARY_BACKSTORY,
        llm=llm or get_llm(temperature=0.2),
        verbose=False,
        allow_delegation=False,
    )
