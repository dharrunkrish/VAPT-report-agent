from crewai import Agent

from config.prompts import SEVERITY_AGENT_BACKSTORY, SEVERITY_AGENT_GOAL
from utils.llm import get_llm


def make_severity_agent(llm=None) -> Agent:
    return Agent(
        role="Vulnerability Severity Classifier",
        goal=SEVERITY_AGENT_GOAL,
        backstory=SEVERITY_AGENT_BACKSTORY,
        llm=llm or get_llm(temperature=0.1),
        verbose=False,
        allow_delegation=False,
    )
