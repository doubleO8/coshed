#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os
import codecs

from bs4 import BeautifulSoup

from .utilities import to_unicode_or_bust


def _n(path):
    """
    Force normalised + unicode for paths

    Args:
        path: path

    Returns:
        unicode: path
    """
    return os.path.normpath(to_unicode_or_bust(path)).replace(os.sep, '/')


def eval_html_sourcefile(item, root=None):
    """
    Evaluate contents of an HTML file for finding references to

        * JavaScript files
        * CSS files
        * image files

    in order to include these files in the distribution archive.

    Args:
        item: tuple or string containing HTML file path
        root: project root

    >>> exf = os.path.abspath(os.path.join(os.path.dirname(__file__), '../contrib/html_example/some.html'))
    >>> root = os.path.dirname(exf)
    >>> len([x for x in eval_html_sourcefile(exf, root=root)])
    2
    """
    if not root:
        root = os.path.dirname(__file__)

    root = os.path.abspath(root)

    try:
        (filename, _) = item
    except ValueError:
        filename = item

    parent = os.path.abspath(os.path.dirname(filename))
    resource_tags = ['script', 'link', 'img']
    with codecs.open(filename, "rb", "utf-8") as source:
        soup = BeautifulSoup(source, 'html.parser')

        for media_ref in soup.find_all(resource_tags):
            if media_ref.get('src') and os.path.isfile(
                    os.path.join(parent, media_ref.get('src'))):
                media_item = media_ref.get("src")
            elif media_ref.get('href') and os.path.isfile(
                    os.path.join(parent, media_ref.get('href'))):
                media_item = media_ref.get("href")
            else:
                continue

            item_abs = os.path.abspath(os.path.join(parent, media_item))
            item_rel = item_abs[len(parent) + 1:]
            yield _n(os.path.join(parent, item_rel)), _n(item_rel)


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))
