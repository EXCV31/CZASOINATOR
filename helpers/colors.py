def get_color(color):
    """
    Function is called when there's need for color, especially for rendering tables.

    Keyword arguments:
    color -- Used in matching color with hex code below.
    """

    if color == "bold_red":
        return "bold #ff4242"
    if color == "red":
        return "#ff4242"
    if color == "bold_orange":
        return "bold #d99011"
    if color == "orange":
        return "#d99011"
    if color == "bold_green":
        return "bold #25ba14"
    if color == "green":
        return "#25ba14"
    if color == "bold_purple":
        return "bold #c071f5"
    if color == "bold_pink":
        return "bold #ff00ee"
    if color == "light_blue":
        return "#6bb0c9"
    if color == "bold_blue":
        return "bold #2070b2"
    if color == "white":
        return "#ffffff"
    if color == "blue":
        return "#2070b2"