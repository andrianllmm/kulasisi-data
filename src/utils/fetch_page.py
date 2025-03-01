import requests
from time import sleep
from typing import Any
from utils.logger import logger
from utils.user_agents import get_random_user_agent


def fetch_page(url: str, retries=0) -> bytes | Any:
    """Fetches a webpage with retries in case of failure, returning the page content."""
    if retries < 0:
        raise ValueError("Number of retries must be a non-negative integer.")

    headers = {"User-Agent": get_random_user_agent()}

    attempt = 0
    while attempt <= retries:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            attempt += 1
            sleep(2 * (attempt + 1))  # Exponentially increasing backoff

    logger.error(f"Failed to fetch {url} after {retries} attempts.")
    return None
