from config.settings import GROQ_API_KEY, GROQ_MODEL, get_logger

from crewai import LLM

logger = get_logger("llm")

_shared_llm: LLM | None = None


def normalize_model_name(model_name: str) -> str:
    """Normalize model names for Groq/LiteLLM."""
    candidate = model_name.strip()

    if not candidate:
        return "groq/openai/gpt-oss-120b"

    if candidate.startswith("groq/"):
        return candidate

    # Preserve the full Groq model ID.
    if candidate.startswith("openai/"):
        return f"groq/{candidate}"

    return f"groq/{candidate}"


def get_llm(temperature: float = 0.2, *, force_new: bool = False) -> LLM:
    """Return a CrewAI-native LLM for Groq (LiteLLM). Reuses one instance by default."""
    global _shared_llm

    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    if _shared_llm is not None and not force_new:
        return _shared_llm

    model_name = normalize_model_name(GROQ_MODEL)
    logger.info("Initializing Groq LLM model=%s temperature=%s", model_name, temperature)

    llm = LLM(
        model=model_name,
        api_key=GROQ_API_KEY,
        temperature=temperature,
    )

    # Prevent CrewAI/instructor from automatically enabling structured/tool outputs
    # by default we'll avoid relying on any LLM-side tool call mechanism. Mark
    # the instance so other code and logs can know structured outputs are disabled.
    try:
        setattr(llm, "_structured_outputs_disabled", True)
        logger.info("Marked LLM structured outputs disabled for safety with Groq.")
    except Exception:
        logger.warning("Could not mark LLM instance with structured outputs flag.")

    if not force_new:
        _shared_llm = llm
    return llm
