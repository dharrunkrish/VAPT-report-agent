from config.settings import GROQ_API_KEY, GROQ_MODEL, get_logger

from crewai import LLM

logger = get_logger("llm")

GROQ_OPENAI_COMPATIBLE_BASE_URL = "https://api.groq.com/openai/v1"

_shared_llm: LLM | None = None


def normalize_model_name(model_name: str) -> str:
    """Normalize model names while preserving explicit Groq-compatible model IDs."""
    candidate = (model_name or "").strip()

    if not candidate:
        return "openai/gpt-oss-120b"

    if candidate.startswith(("groq/", "openai/")):
        return candidate

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
        base_url=GROQ_OPENAI_COMPATIBLE_BASE_URL,
        custom_llm_provider="groq",
        temperature=temperature,
        tool_choice="none",
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
