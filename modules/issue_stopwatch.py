import calendar
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import logging
import redminelib

# File imports
from config.setup_config_and_connection import redmine
from database.setup_db import cursor, conn
from helpers.colors import get_color
from config.setup_config_and_connection import frame_title
from helpers.convert_float import float_to_hhmm
from helpers.get_today_or_yesterday import get_time
from helpers.error_handler import display_error

console = Console()
logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')


def start_issue_stopwatch():
    """
    The function is responsible for measuring the time for the task selected by the user.
    After the measurement is completed, it places the collected data in redmine and database.

    Returns:
    """

    # Stop variable is used to stop the stopwatch.
    stop = ""

    issue_id = input("\nPodaj numer zadania > ")

    # Start stopwatch
    start_timestamp = int(calendar.timegm(time.gmtime()))

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))
    except redminelib.exceptions.ForbiddenError:
        display_error("403 - Brak dostępu do wybranego zadania!")
        return
    except redminelib.exceptions.ResourceNotFoundError:
        display_error("404 - Wybrane zadanie nie istnieje!")
        return

    console.print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                            style=get_color("light_blue"), title=frame_title),
                  "")
    logging.info(f"Rozpoczęto mierzenie czasu dla zadania #{issue_id}")

    # Wait for input from user, to stop the stopwatch.
    console.print(f'[{get_color("bold_green")}]Rozpoczęto mierzenie czasu![/{get_color("bold_green")}]')
    while stop != "k":
        stop = console.input(
            f'\nGdy zakończysz pracę nad zadaniem wpisz [{get_color("bold_green")}]k[/{get_color("bold_green")}], '
            f'lub [{get_color("bold_red")}]x[/{get_color("bold_red")}] aby anulować > ')
        if stop.lower() == "x":
            return
    logging.info(f"Zakończono mierzenie czasu dla zadania #{issue_id}")

    # Stop stopwatch and calculate timestamp to hours e.g 2.63.
    stop_timestamp = int(calendar.timegm(time.gmtime()))
    float_time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)
    time_elapsed = float_to_hhmm(float_time_elapsed)

    console.print("", Panel(
        Text(f"\nZakończono pracę nad #{issue_id}!\n Spędzony czas: {time_elapsed}\n ", justify="center",
             style="white"), style=get_color("light_blue"),
        title="[bold orange3]CZASOINATOR"))

    comment = input("\nDodaj komentarz > ")

    decision = input("Dodać czas do zadania w redmine? T/n > ")
    if decision.lower() == "t" or decision == "":
        current_time, _, today = get_time()

        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=today,
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except Exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")
            logging.error(e)
            return

        logging.info(f"Dodano czas do redmine dla zadania #{issue_id}.")

        console.print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {time_elapsed}"
                                     f"\nKomentarz: {comment}\n",
                                     justify="center", style="white"), style=get_color("green"),
                                title=frame_title))

        # Insert user work to database.
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, float_time_elapsed, comment))
        logging.info("Umieszczono przepracowany czas w bazie danych.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zacommitowano zmiany w bazie danych.")
