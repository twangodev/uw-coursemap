import random

def compute_relative_luminance(color):
    """
    Compute the relative luminance of a hex color according to WCAG guidelines.

    Args:
        color (str): A hex color string in the form "#RRGGBB".

    Returns:
        float: The relative luminance value.
    """
    # Remove '#' if present
    if color.startswith("#"):
        color = color[1:]
    # Convert hex to RGB and normalize to 0-1 range
    r = int(color[0:2], 16) / 255.0
    g = int(color[2:4], 16) / 255.0
    b = int(color[4:6], 16) / 255.0

    # Apply gamma correction
    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r_lin = adjust(r)
    g_lin = adjust(g)
    b_lin = adjust(b)

    # Compute relative luminance using the standard coefficients
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def is_contrasting(color, min_ratio=4.5):
    """
    Check if the provided hex color meets the Material Design contrast ratio standards against a white background.

    This function calculates the contrast ratio using the WCAG formula:
        contrast ratio = (L_light + 0.05) / (L_dark + 0.05)
    Since white (with relative luminance 1.0) is the background, if our color is darker,
    the ratio becomes (1.0 + 0.05) / (L_color + 0.05).

    Args:
        color (str): A hex color string in the form "#RRGGBB".
        min_ratio (float): The minimum required contrast ratio. Defaults to 4.5.

    Returns:
        bool: True if the color meets the contrast ratio requirement, else False.
    """
    L = compute_relative_luminance(color)
    # White has a luminance of 1.0
    contrast = (1.0 + 0.05) / (L + 0.05)
    return contrast >= min_ratio

def generate_random_hex_colors(parents, color_map):
    """
    For each parent in the set, use its existing color from color_map if available;
    otherwise, generate a new random hex color that meets Material Design's contrast
    requirements against a white background, update the color_map, and add it to the result list.

    Args:
        parents (set of str): Set of parent identifiers.
        color_map (dict): Mapping from a parent identifier to a hex color string.

    Returns:
        list: A list of hex color strings corresponding to the parents.
    """
    colors = []
    for parent in parents:
        if parent in color_map:
            colors.append(color_map[parent])
        else:
            # Generate a new random color until one meets the contrast requirement
            while True:
                random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                if is_contrasting(random_color):
                    break
            color_map[parent] = random_color
            colors.append(random_color)
    return colors
