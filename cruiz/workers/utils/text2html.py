#!/usr/bin/env python3

"""
Converting text to HTML
"""

import html as html_module

from io import StringIO


def text_to_html(text: str, spaces_per_tab: int = 4) -> str:
    """
    Break a block of text into text and HTML markup.
    """
    html = StringIO()
    stripped_line = text.lstrip()
    num_leading_chars = len(text) - len(stripped_line)
    for index in range(num_leading_chars):
        current_char = text[index]
        if current_char == " ":
            html.write("&nbsp;")
        elif current_char == "\t":
            html.write(spaces_per_tab * "&nbsp;")
        elif current_char in ("\r", "\n"):
            continue  # dealt with later
        else:
            raise RuntimeError(
                f"Unrecognised space character: '{current_char}' "
                f"({ord(current_char)}), in the text '{text}'"
            )
    escaped = html_module.escape(stripped_line)
    escaped = escaped.replace(" ", "&nbsp;")
    html.write(escaped)
    html_str = html.getvalue()
    html_str = html_str.replace("\n", "<br>")
    html_str = html_str.replace("\t", 4 * "&nbsp;")
    return html_str
