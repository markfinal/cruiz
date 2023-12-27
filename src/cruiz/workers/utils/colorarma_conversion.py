#!/usr/bin/env python3

"""
Util module to convert colorama escpe codes to HTML
"""

import copy
from io import StringIO
import re

import colorama

from .text2html import text_to_html


def convert_from_colorama_to_html(escaped_string: str) -> str:
    """
    Attempt to convert colorama escape sequences into something that HTML can use
    """
    # pylint: disable=anomalous-backslash-in-string,too-many-branches
    if escaped_string.endswith("\n"):
        # last new line is catered for by the HTML block
        escaped_string = escaped_string.rsplit("\n", 1)[0]
    expr = r"(\x1b\[(\d)+m)"  # ESC[NUMm - find NUM
    matches = re.findall(expr, escaped_string)
    non_escaped_string = copy.deepcopy(escaped_string)
    style = None
    foreground_colour = None
    for match in matches:
        code = match[0]
        if code == colorama.Style.BRIGHT:
            style = ("<strong>", "</strong>")
        elif code == colorama.Fore.BLACK:
            foreground_colour = ('<font color="black">', "</font>")
        elif code == colorama.Fore.RED:
            foreground_colour = ('<font color="red">', "</font>")
        elif code == colorama.Fore.GREEN:
            foreground_colour = ('<font color="green">', "</font>")
        elif code == colorama.Fore.YELLOW:
            foreground_colour = ('<font color="yellow">', "</font>")
        elif code == colorama.Fore.BLUE:
            foreground_colour = ('<font color="blue">', "</font>")
        elif code == colorama.Fore.MAGENTA:
            foreground_colour = ('<font color="magenta">', "</font>")
        elif code == colorama.Fore.CYAN:
            foreground_colour = ('<font color="cyan">', "</font>")
        elif code == colorama.Fore.WHITE:
            foreground_colour = ('<font color="white">', "</font>")
        else:
            pass
        non_escaped_string = non_escaped_string.replace(match[0], "")

    html = StringIO()
    if foreground_colour:
        html.write(foreground_colour[0])
    if style:
        html.write(style[0])
    html.write(text_to_html(non_escaped_string))
    if style:
        html.write(style[1])
    if foreground_colour:
        html.write(foreground_colour[1])
    return html.getvalue()
