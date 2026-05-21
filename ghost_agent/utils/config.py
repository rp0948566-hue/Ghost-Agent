import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    headless: bool = field(default_factory=lambda: os.getenv("GHOST_HEADLESS", "true").lower() == "true")
    slow_mo: int = field(default_factory=lambda: int(os.getenv("GHOST_SLOW_MO", "0")))
    timeout: int = field(default_factory=lambda: int(os.getenv("GHOST_TIMEOUT", "30000")))
    screenshot_dir: str = field(default_factory=lambda: os.getenv("GHOST_SCREENSHOT_DIR", "screenshots"))
    max_steps: int = field(default_factory=lambda: int(os.getenv("GHOST_MAX_STEPS", "20")))
    browser: str = field(default_factory=lambda: os.getenv("GHOST_BROWSER", "chromium"))

    def validate(self):
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Create a .env file or export the environment variable."
            )
        if self.browser not in ("chromium", "firefox", "webkit"):
            raise ValueError(f"Unsupported browser: {self.browser}. Choose chromium, firefox, or webkit.")
        return self
