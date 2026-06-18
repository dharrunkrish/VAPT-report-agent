from crewai import Agent

from config.prompts import REPORT_WRITER_BACKSTORY, REPORT_WRITER_GOAL
from utils.llm import get_llm


def make_report_writer_agent(llm=None) -> Agent:
    return Agent(
        role="VAPT Report Writer",
        goal=REPORT_WRITER_GOAL,
        backstory=REPORT_WRITER_BACKSTORY,
        llm=llm or get_llm(temperature=0.2),
        verbose=False,
        allow_delegation=False,
    )
