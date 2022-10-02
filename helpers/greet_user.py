import logging
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
import requests.exceptions
import redminelib.exceptions
import platform
import subprocess
import time

# File imports
from helpers.colors import get_color
from config.setup_config_and_connection import redmine, frame_title
from helpers.error_handler import display_error
from helpers.exit_handler import exit_program

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')

console = Console()


def welcome():
    """
    Log into redmine and greet user. Also, here we have error handler, for auth, connection and permission errors.

    Returns:

    """
    console.rule(
        f"[{get_color('bold_orange')}]CZASOINATOR [{get_color('white')}]-"
        f" [{get_color('blue')}]Trwa ładowanie aplikacji...", )

    # Check if connection is OK.
    try:
        user = redmine.user.get('current')
    except requests.exceptions.ConnectionError:
        display_error("Wystąpił problem z połączeniem do Redmine. Sprawdź stan sieci!")
        exit_program(1)
    except redminelib.exceptions.AuthError:
        display_error("Użyto nieprawidłowych danych logowania!")
        exit_program(1)
    except redminelib.exceptions.ForbiddenError:
        display_error("Brak dostępu do danych API! Skontaktuj się z administratorem sieci.")
        exit_program(1)

    # Clear terminal
    if platform.system() == "Linux" or platform.system() == "Darwin":
        subprocess.run("clear")
    else:
        subprocess.run("cls")

    logging.info(f"Połączenie zakończone sukcesem. Zalogowany jako {user.firstname} {user.lastname}")

    console.print(Panel(Text("\nZalogowano pomyślnie!\n"
                             f"\nUżytkownik: {user.firstname} {user.lastname}"
                             f"\nNa Redmine od: {str(user.created_on)}\n", justify="center", style="white"),
                        style=get_color("green"), title=frame_title))

    # It just better look with that.
    time.sleep(0.5)
