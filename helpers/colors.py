def get_color(color):
    """
    Function is called when there's need for color, especially for rendering tables.

    Args:
        color: Used in matching color with hex code below.

    Returns: Hex code of desired color.

    """

    match color:
        case "bold_red":
            return "bold #ff4242"
        case "red":
            return "#ff4242"
        case "bold_orange":
            return "bold #d99011"
        case "orange":
            return "bold #d99011"
        case "bold_green":
            return "bold #25ba14"
        case "green":
            return "#25ba14"
        case "bold_purple":
            return "bold #c071f5"
        case "bold_pink":
            return "bold #ff00ee"
        case "light_blue":
            return "#6bb0c9"
        case "bold_blue":
            return "bold #2070b2"
        case "blue":
            return "#2070b2"
        case "white":
            return "#ffffff"
