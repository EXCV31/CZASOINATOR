from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import re
import logging
import redminelib

# File imports
from config.setup_config_and_connection import redmine, frame_title
from database.setup_db import cursor, conn
from helpers.get_today_or_yesterday import get_time
from helpers.colors import get_color
from helpers.error_handler import display_error

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
console = Console()


def add_manually_to_redmine():
    """
    A function used to add manually to redmine hours worked.

    Returns:

    """

    current_time, _, today = get_time()
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))

    except redminelib.exceptions.ForbiddenError:
        display_error("403 - Brak dostępu do wybranego zadania!")
        return

    except redminelib.exceptions.ResourceNotFoundError:
        display_error("404 - Wybrane zadanie nie istnieje!")
        return

    console.print("",
                  Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                        style=get_color("light_blue"), title=frame_title))

    question = input("\nKontynuować? T/n > ")

    if question.lower() == "t" or question == "":

        # This variable is used in database.
        time_elapsed = input("\nPodaj czas spędzony nad zadaniem w formacie H:MM - np 2:13 > ")

        # Check if user pass time in correct format.
        if not bool(re.match(r"\d:\d\d", time_elapsed)):
            display_error("Nieprawidłowa wartość dla pola: Spędzony czas")
            return

        # Convert H:MM to float - eg 0:45 -> 0.80
        hours, minutes = time_elapsed.split(":")
        float_time_elapsed = round((int(hours) + float(minutes) / 60), 2)

        comment = input("Dodaj komentarz > ")
        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=today,
                                      hours=float_time_elapsed, activity_id=8, comments=comment)
        except Exception as e:
            console.print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        logging.info(
            f"Dodano manualnie przepracowany czas do redmine pod zadaniem #{issue_id} - {time_elapsed} godzin.")
        # Insert user work to database.
        cursor.execute("INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       "(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, float_time_elapsed, comment,))
        logging.info(
            f"Umieszczono w bazie danych dodany manualnie przepracowany czas pod zadaniem "
            f"#{issue_id} - {float_time_elapsed} godzin.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zakommitowano zmiany w bazie danych.")

        console.print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {hours} godzin, {minutes} minut."
                                     f"\nKomentarz: {comment}\n", justify="center", style="white"),
                                style=get_color("green"),
                                title=frame_title))
