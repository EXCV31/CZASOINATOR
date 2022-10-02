import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

# File imports
from database.setup_db import cursor
from config.setup_config_and_connection import redmine_conf, frame_title
from helpers.colors import get_color
from helpers.convert_float import float_to_hhmm

console = Console()

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')


def show_work(day):
    """
    A feature that shows progress and time spent on all tasks on the given day.

    Args:
        day: The day from which the script should show the work. Possible values: Today or yesterday.

    Returns:
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
                            title=frame_title))

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
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{row[1]}]"
                          f"#{row[1]}[/link][/{get_color('light_blue')}]")
    total_hours = float_to_hhmm(total_hours)
    table.caption = f"Sumaryczny czas w tym dniu: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut"

    # Show table with work time.
    console.print(table)
