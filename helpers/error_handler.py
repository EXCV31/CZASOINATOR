import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from helpers.colors import get_color
from config.setup_config_and_connection import frame_title

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
console = Console()
def display_error(text):
    """
    Function used for displaying errors - normal and critical. Often used before exit_program().

    Keyword arguments:
    text -- Text of error displayed in frame.
    """
    print("")
    console.print(
        Panel(Text(f"\n{text}\n", justify="center", style="white"), style=get_color("red"), title=frame_title))
    logging.error(text)