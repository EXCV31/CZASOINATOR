import datetime


def get_time():
    """
    Return current time, yesterday and today. If today is Monday,
    function will return Friday as yesterday.

    Returns:
        current_time: Current time in format YYYY-MM-DD HH:MM:SS
        yesterday: Yesterday in format YYYY-MM-DD
        today: Today in format YYYY-MM-DD

    """
    # Get and format current date
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Check if today is monday - used for valid "yesterday" when it's weekend. If today is monday, yesterday is friday.
    if now.weekday() == 0:
        yesterday = now - datetime.timedelta(days=3)
        yesterday = str(yesterday).split(" ")[0]
    else:
        yesterday = now - datetime.timedelta(days=1)
        yesterday = str(yesterday).split(" ")[0]

    # Split current time from 2021-12-10 22:32:52 to 2021-12-10
    today = current_time.split(" ")[0]

    return current_time, yesterday, today
