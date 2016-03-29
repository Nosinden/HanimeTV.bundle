#!/usr/bin/env python

"""
common code for Hanime.tv
currently used to preload the Base Search URL
"""

def load_search_url(url):
    """Get current Base Search URL"""

    html = HTML.ElementFromURL(url)

    d = None
    search_url = False
    for node in html.xpath('//script'):
        node_text = node.text_content()
        match = Regex('water\ \=(.*)').search(node_text)
        if match:
            d = JSON.ObjectFromString(match.group(1).strip().rstrip(';'))
            break

    if d:
        search_url = d['env']['search_base_url']

    return search_url
