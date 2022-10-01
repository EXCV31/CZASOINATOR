import requests.exceptions
import redminelib.exceptions
import calendar
import time
from datetime import date
import sys

from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import BarColumn, Progress, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
import configparser
import logging
from timeit import default_timer as timer
import re
import platform
import subprocess

# File imports
from config.setup_config_and_connection import redmine, redmine_conf, frame_title
from database.setup_db import conn, cursor
from helpers.colors import get_color
from helpers.get_today_or_yesterday import get_time
from helpers.convert_float import float_to_hhmm
from helpers.error_handler import display_error
from helpers.exit_handler import exit_program
from helpers.options import show_options
from modules.days_off import show_days_off
from modules.issue_stopwatch import start_issue_stopwatch

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')

stop = ""
choose = 0
info = False
console = Console()

logging.info("Aplikacja została uruchomiona")


def welcome_user():
    """Parse config, log into redmine and greet user."""
    console.rule(
        f"[{get_color('bold_orange')}]CZASOINATOR [{get_color('white')}]- [{get_color('blue')}]Trwa ładowanie aplikacji...", )

    try:
        user = redmine.user.get('current')
    except requests.exceptions.ConnectionError:
        display_error("Wystąpił problem z połączeniem do Redmine. Sprawdź stan sieci!")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program(1)
    except redminelib.exceptions.AuthError:
        display_error("Użyto nieprawidłowych danych logowania!")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program(1)
    except redminelib.exceptions.ForbiddenError:
        display_error("Brak dostępu do danych API! Skontaktuj się z administratorem sieci.")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program(1)

    # Clear terminal
    if platform.system() == "Linux" or platform.system() == "Darwin":
        subprocess.run("clear")
    else:
        subprocess.run("cls")

    logging.info(f"Połączenie zakończone sukcesem. Zalogowany jako {user.firstname} {user.lastname}")

    console.print(Panel(Text("\nZalogowano pomyślnie!\n"
                             f"\nUżytkownik: {user.firstname} {user.lastname}"
                             f"\nNa Redmine od: {str(user.created_on)}\n", justify="center", style="white")
                        , style=get_color("green"), title=frame_title))

    # It just better look with that.
    time.sleep(0.5)
    return redmine


def show_work(cursor, day):
    """
    Some magic happeened here!
    With user input from get_started() day variable is set to today or yesterday.
    It's set by choosing in "if __name__ == __main__" by get_time function
    which returns current time, yesterday and today.
    """

    total_hours = 0

    # This variable store information about doing anything before daily.
    info_daily = False

    # Replace 11:00:00 from config.ini to 110000. It's needed for comparing time, used to render "daily" row in table.
    daily = redmine_conf["DAILY"].replace(":", "")

    # Send query to get data from today.
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA LIKE ?", (f"%{day}%",))

    # Fetch data from query above.
    rows = cursor.fetchall()
    logging.info("Pobrano dane z bazy danych dotyczące przepracowanych godzin dzisiejszego lub wczorajszego dnia.")

    # Empty rows variable means there's no SQL entries.
    if not rows:
        console.print("",
                      Panel(Text("\n Brak postępów! \n", justify="center", style="white"), style=get_color("orange"),
                            title="[bold orange3]CZASOINATOR"))

        return

    # Generate column to show data from SQL.
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f'[{get_color("bold_blue")}]POSTĘPY DNIA {day}', show_lines=True, box=box.DOUBLE, expand=True)

    table.add_column("Data rozpoczęcia", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Komentarz", justify="center")
    table.add_column("Numer zadania", justify="center")

    for row in rows:
        total_hours += float(row[3])

        # Set up colors for spent time.
        # 00:00-02:00 - Green
        # 02:00-04:00 - Orange
        # 04:00+ - Red
        if float(row[3]) <= 2.00:
            color = get_color("bold_green")
        elif float(row[3]) <= 4.00:
            color = get_color("bold_orange")
        else:
            color = get_color("bold_red")

        # Split row with date: 24-11-2021 14:20:52 -> 14:20:52.
        # Drop ":" from split data above, and compare it with daily variable.
        # Also check if "daily lines" are displayed before.
        if row[0].split(" ")[1].replace(":", "") > daily and info_daily is False:
            table.add_row(f'{day} {redmine_conf["DAILY"]}',
                          f'[{get_color("bold_pink")}]Daily![/{get_color("bold_pink")}]', '', '',
                          f'')
            info_daily = True

        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Empty issue number".
        row_1 = row[1]

        # Same as above, eg 4.86 -> 04:51.
        time_spent = float_to_hhmm(float(row[3]))

        # Append row to table with recognizing that info about work has issue number.
        if row_1 is None:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('bold_red')}]Brak![/{get_color('bold_red')}]")
        else:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{row[1]}]#{row[1]}[/link][/{get_color('light_blue')}]")
    total_hours = float_to_hhmm(total_hours)
    table.caption = f"Sumaryczny czas w tym dniu: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut"
    # Show table with work time.
    console.print(table)

    # Close connection to database.
    conn.close()


def add_manually_to_redmine(redmine, cursor):
    """
    A function used to add manually to redmine hours worked.

    Keyword arguments:
    redmine -- Connection to redmine.
    cursor  -- Cursor for executing SQL commands.
    """
    current_time, _, today = get_time()
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))

    except redminelib.exceptions.ForbiddenError:
        display_error(f"403 - Brak dostępu do zadania {issue_id}!")
        return

    except redminelib.exceptions.ResourceNotFoundError:
        display_error(f"404 - zadanie {issue_id} nie istnieje!")
        return

    console.print("",
                  Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                        style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))

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
            f"Umieszczono w bazie danych dodany manualnie przepracowany czas pod zadaniem #{issue_id} - {float_time_elapsed} godzin.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zakommitowano zmiany w bazie danych.")
        conn.close()

        console.print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {hours} godzin, {minutes} minut."
                                     f"\nKomentarz: {comment}\n", justify="center", style="white"),
                                style=get_color("green"),
                                title="[bold orange3]CZASOINATOR"))


def show_assigned_to_user(redmine):
    """
    The function is to connect to redmine, and retrieve all tasks
    in "Open" status that are assigned to the user.
    The function also includes a filter that skips tasks that are
    in projects defined in config.ini, in the "EXCLUDE" section.

    Keyword arguments:
    redmine      -- Connection to redmine.
    """

    progress_columns = (
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        "Minęło:",
        TimeElapsedColumn(),
        "Pozostało:",
        TimeRemainingColumn(),
    )

    # "total" variable is used to represent hours spent on each issue.
    total = 0

    # Get user ID from redmine by api key
    user = redmine.user.get('current')
    user_name = str(user)
    user_id = user["id"]

    # Generate column to show data from redmine
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f"[{get_color('bold_blue')}]Zadania przypisane do: {user_name}, ID: {user_id}",
                  show_lines=True, box=box.DOUBLE, expand=True)

    table.add_column("Typ zadania", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Priorytet", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("% ukończenia", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Numer zadania", justify="center")

    logging.info("Rozpoczęto przetwarzanie zadań przypisanych do użytkownika...")
    start = timer()

    # Filter issues with "open" status assigned to use, excluding groups.
    issues = redmine.issue.filter(assigned_to_id=user_id)

    if len(issues) > 0:
        # Progress bar section. Progress bar has two attributes:
        # task   -- is one and only progress bar.
        # update -- function used to update progress bar in each iteration over list of issues.
        with Progress(*progress_columns, expand=True) as progress_bar:
            counter = 0
            
            # Formatting :)
            console.print("")

            # Add a proggress bar.
            task = progress_bar.add_task(f"[{get_color('blue')}]Pobieranie danych...", total=len(issues))
            for issue in issues:

                # Updating progress bar before processing issue, because of EXCLUDE "if" below.
                counter +=1
                progress_bar.update(task, advance=1, description=f"[{get_color('blue')}]Pobieranie danych - {counter} / {len(issues)}")
                
                # Delay for progress bar pretty-print.
                time.sleep(0.001)

                # Skip project name if any mentioned in config.ini.
                if issue.project["name"] in redmine_conf["EXCLUDE"].split("\n"):
                    continue

                # Color matching by priority.
                if str(issue.priority) == "Niski":
                    priority_color = get_color("bold_green")
                elif str(issue.priority) == "Normalny":
                    priority_color = get_color("bold_orange")
                else:
                    priority_color = get_color("bold_red")

                # Color matching by % of completion.
                if issue.done_ratio >= 66:
                    done_color = get_color("bold_green")
                elif issue.done_ratio >= 33:
                    done_color = get_color("bold_orange")
                else:
                    done_color = get_color("bold_red")

                # Color matching by issue status.
                if str(issue.status) == "Zablokowany":
                    status_color = get_color("bold_red")
                else:
                    status_color = "white"

                # Get data about hours worked and put in total variable.
                for time_entry in issue.time_entries:
                    info = redmine.time_entry.get(time_entry)
                    total += info.hours

                # Convert float time to HH:MM
                time_spent = float_to_hhmm(round(total, 2))

                # Add a row to the table to display it after data collection.
                table.add_row(f"{issue.tracker['name']}",
                              f"{issue.subject}",
                              f"[{priority_color}]{issue.priority}[/{priority_color}]",
                              f"[{status_color}]{str(issue.status)}[/{status_color}]",
                              f"[{done_color}]{str(issue.done_ratio)}[/{done_color}]",
                              f"{time_spent}",
                              f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{issue.id}]#{issue.id}[/link][/{get_color('light_blue')}]")

                # Reset variable for next issue.
                total = 0

            end = timer()
            logging.info(f"Zakończono przetwarzanie zadań przypisanych do usera. Czas operacyjny: {end - start} sekund")

            # Show table with issues.
        console.print("", table)

    else:
        end = timer()
        logging.info(
            f"Zakończono przetwarzanie zadań przypisanych do usera. Brak danych do wyświetlenia. Czas operacyjny: {end - start} sekund")
        console.print("", Panel(Text(f"\nBrak zadań przypisanych do: {user_name}, {user_id}\n", justify="center",
                                     style=get_color("bold_red")),
                                title=frame_title))


def stats(cursor):
    """
    Show stats about usage to user - data is taken from database, not from redmine.

    Keyword arguments:
    cursor  -- Cursor for executing SQL commands.
    """
    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])

    # Convert float time to HH:MM
    total_hours = float_to_hhmm(total_hours)

    console.print("", Panel(Text(
        f"\n Czas spędzony z CZASOINATOREM: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut\n",
        justify="center", style="white"),
        style=get_color("light_blue"), title=frame_title))


if __name__ == "__main__":
    redmine = welcome_user()
    info = True
    while True:
        if info is True:
            show_options()
            info = False
    
        choose = input("\nWybór > ")
        
        if choose == str(1):
            start_issue_stopwatch()
        if choose == str(2):
            _, _, day = get_time()
            show_work(cursor, day)
        if choose == str(3):
            _, day, _ = get_time()
            show_work(cursor, day)
        if choose == str(4):
            add_manually_to_redmine(redmine, cursor)
        if choose == str(5):
            show_assigned_to_user(redmine)
        if choose == str(6):
            show_days_off()
        if choose == str(7):
            stats(cursor)
        if choose == str(8):
            exit_program(0)
        if choose == "?":
            info = True
