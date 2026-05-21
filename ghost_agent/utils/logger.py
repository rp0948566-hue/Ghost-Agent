import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()

def get_logger(name: str = "ghost-agent") -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    return logging.getLogger(name)
