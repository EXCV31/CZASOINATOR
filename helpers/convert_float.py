def float_to_hhmm(float_time):
    """
    Convert float time to HH:MM format. 1.75 => 1:45.

    Args:
        float_time: time in float.

    Returns: Time in HH:MM format.

    """

    # Multiply float time by 60 to get minutes, split into hours and minutes
    float_time = float_time * 60
    hours, minutes = divmod(float_time, 60)

    # Drop floating points numbers e.g. 41.39999999999998 -> 41,
    # then cast to str to add trailing or leading zero - to get always 2-digit minutes.
    minutes = str(int(minutes))
    if len(minutes) == 1 and minutes.startswith("0"):
        minutes += "0"
    elif len(minutes) == 1 and int(minutes) > 0:
        minutes = "0" + minutes

    return f"{int(hours)}:{minutes}"
