from crewai import Agent

from config.prompts import FINDING_ANALYSIS_BACKSTORY, FINDING_ANALYSIS_GOAL
from utils.llm import get_llm


def make_finding_analysis_agent(llm=None) -> Agent:
    return Agent(
        role="VAPT Finding Analyst",
        goal=FINDING_ANALYSIS_GOAL,
        backstory=FINDING_ANALYSIS_BACKSTORY,
        llm=llm or get_llm(temperature=0.15),
        verbose=False,
        allow_delegation=False,
    )
