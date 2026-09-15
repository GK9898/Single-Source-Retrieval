import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

def log_retry_attempt(retry_state):
    """Log retry attempts for tenacity decorators."""
    logger.warning(
        f"Retry attempt #{retry_state.attempt_number} for {retry_state.fn.__name__} "
        f"after exception: {retry_state.outcome.exception()}"
    )

def llm_retry_decorator(max_attempts=3, min_wait=1, max_wait=10):
    """Tenacity retry decorator configured for LLM/API calls."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((Exception,)),
        after=log_retry_attempt,
        reraise=True
    )
