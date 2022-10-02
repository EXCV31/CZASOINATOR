from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import logging

# File imports
from config.setup_config_and_connection import frame_title
from helpers.colors import get_color

console = Console()
logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')


def show_options():
    """
    Point where program start with user interaction.

    Returns:

    """

    console.print(Panel(Text("\nWybierz co chcesz zrobić:\n"
                             "\n1. Uruchom zliczanie czasu"
                             "\n2. Sprawdź dzisiejsze postępy"
                             "\n3. Sprawdź wczorajsze postępy"
                             "\n4. Dorzuć ręcznie czas do zadania"
                             "\n5. Sprawdź zadania przypisane do Ciebie"
                             "\n6. Sprawdź swoje dni urlopowe"
                             "\n7. Statystyki"
                             "\n8. Wyjście\n", justify="center", style="white"), style=get_color("light_blue"),
                        title=frame_title))
    logging.info("Pokazano listę opcji do wyboru.")
