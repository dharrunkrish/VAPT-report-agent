from crewai import LLM

from config.settings import GROQ_API_KEY, GROQ_MODEL, get_logger

logger = get_logger("llm")

_shared_llm: LLM | None = None


def get_llm(temperature: float = 0.2, *, force_new: bool = False) -> LLM:
    """Return a CrewAI-native LLM for Groq (LiteLLM). Reuses one instance by default."""
    global _shared_llm

    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    if _shared_llm is not None and not force_new:
        return _shared_llm

    model_name = GROQ_MODEL if GROQ_MODEL.startswith("groq/") else f"groq/{GROQ_MODEL}"
    logger.info("Initializing Groq LLM model=%s temperature=%s", model_name, temperature)

    llm = LLM(
        model=model_name,
        api_key=GROQ_API_KEY,
        temperature=temperature,
    )

    if not force_new:
        _shared_llm = llm
    return llm
