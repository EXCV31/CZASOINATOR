import logging
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich import box
from timeit import default_timer as timer
import time

# File imports 
from config.setup_config_and_connection import redmine, redmine_conf, frame_title
from helpers.colors import get_color
from helpers.convert_float import float_to_hhmm

console = Console()


def show_assigned_to_user():
    """
    The function is to connect to redmine, and retrieve all tasks
    in "Open" status that are assigned to the user.
    The function also includes a filter that skips tasks that are
    in projects defined in config.ini, in the "EXCLUDE" section.

    Returns:

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
                counter += 1
                progress_bar.update(task, advance=1, description=f"[{get_color('blue')}]Pobieranie danych"
                                                                 f" - {counter} / {len(issues)}")

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
            f"Zakończono przetwarzanie zadań przypisanych do usera. Brak danych do wyświetlenia."
            f" Czas operacyjny: {end - start} sekund")
        console.print("", Panel(Text(f"\nBrak zadań przypisanych do: {user_name}, {user_id}\n", justify="center",
                                     style=get_color("bold_red")),
                                title=frame_title))
