#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIT
---

Helper functions for interacting with
`git <http://git-scm.com/>`_.
"""
from __future__ import print_function
from past.builtins import cmp
from builtins import zip
import re
import logging
from subprocess import PIPE, Popen
import copy

#: regular expression for 'official' tags
OFFICIAL_TAG_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)"
    r"\.(?P<patch>\d+)(\.(?P<build>\d+))?"
    r"(\-(?P<git_describe>[\d\w\-]+))?$"
)

#: regular expression for changelog entries
LOG_RE = re.compile(
    r"^\[(?P<tag>.*?)\] (?P<hash>[\w\d]+) "
    r"(?P<date>\d{4}\-\d{2}\-\d{2}) \[(?P<author>.*?)\] "
    r"(?P<msg>.*?)$"
)

#: regular expression for entries to be considered as 'junk'
MSG_JUNK_RE = re.compile(r"^git\-svn\-id\:|^[\s\.]+$")

#: changelog file lines format
OUTPUT_LOG_FORMAT = "%(date)s %(author)s %(ver)-9s %(hash)s %(msg)s"

#: version portions
PORTIONS = ["major", "minor", "patch", "build"]

LOG = logging.getLogger(__name__)


def git_current_tag(raw=False):
    """
    Retrieve current git tag.

    :param raw: return entire tag as string
    :return: current tag
    :rtype: list
    :rtype: str

    >>> len(git_current_tag())
    1
    >>> git_current_tag(True) == git_current_tag()[0]
    True
    """
    lines = (
        Popen("git describe", shell=True, stdout=PIPE)
        .communicate()[0]
        .decode("utf-8")
        .split("\n")
    )
    if raw is True:
        return lines[0]
    return lines[0].split("-", 1)


def git_tag_tuple(line=None):
    """
    Retrieve current git tag (as tuple).

    :param line: version string
    :return: version information or None
    :rtype: tuple

    >>> git_tag_tuple("") is None
    True
    >>> git_tag_tuple("1.2.3")
    (1, 2, 3, 0)
    """
    m = re.match(OFFICIAL_TAG_RE, line)
    if m:
        gdict = git_tag_dict(line)
        return (
            gdict.get("major"),
            gdict.get("minor"),
            gdict.get("patch"),
            gdict.get("build"),
        )
    return None


def git_tag_dict(line=None):
    """
    Parse an 'official' git tag and return a ``dict()`` containing retrieved
    values.

    Returns an empty dict if data could not be parsed.

    :param line: version string
    :return: version information or empty dict
    :rtype: dict

    >>> dd1 = git_tag_dict("")
    >>> dd1.get("major") is None
    True
    >>> dd2 = git_tag_dict("1.2.3")
    >>> dd2.get('major')
    1
    >>> dd2.get('build')
    0
    >>> dd3 = git_tag_dict("0.0.0.1")
    >>> dd3.get("build")
    1
    >>> dd3.get("major") == dd3.get("minor") == dd3.get("patch") == 0
    True
    >>> dd4 = git_tag_dict()
    >>> dd4.get("major") is not None
    True
    """
    if line is None:
        line = git_current_tag()[0]

    m = re.match(OFFICIAL_TAG_RE, line)
    if m:
        gdict = m.groupdict()
        for key in PORTIONS:
            val = gdict.get(key, 0)
            if val is None:
                val = 0
            gdict[key] = int(val)
        return gdict
    return dict()


def git_official_tags():
    otags = list()

    lines = (
        Popen("git tag -l", shell=True, stdout=PIPE)
        .communicate()[0]
        .split("\n")
    )
    for line in lines:
        tag_tuple = git_tag_tuple(line)
        if tag_tuple:
            otags.append(tag_tuple)
    return list(reversed(sorted(otags)))


def git_official_tags_raw():
    otags = list()

    lines = (
        Popen("git tag -l", shell=True, stdout=PIPE)
        .communicate()[0]
        .split("\n")
    )
    for line in lines:
        m = re.match(OFFICIAL_TAG_RE, line)
        if m:
            gdict = m.groupdict()
            otags.append(gdict)
    return list(reversed(sorted(otags)))


def git_tag_string(tag_dict, plain_int=False):
    """
    Normalise version information in *tag_dict*.

    :param tag_dict: version information
    :return: normalised version string
    :rtype: str

    >>> git_tag_string(git_tag_dict("1.2.15.99"))
    '1.2.15.099'
    >>> git_tag_string(git_tag_dict("1.2.15.99"), plain_int=True)
    '1.2.15.99'
    >>> git_tag_string(git_tag_dict("1.2.0"))
    '1.2.0'
    """
    for key in PORTIONS:
        val = tag_dict.get(key)
        if val is not None:
            val = int(val)
        tag_dict[key] = val

    parts = ["{major:d}.{minor:d}.{patch:d}".format(**tag_dict)]
    if tag_dict.get("build"):
        parts.append(
            (plain_int and "{build:d}" or "{build:03d}").format(**tag_dict)
        )
    return ".".join(parts)


def git_official_tag_property(tag_tuple):
    for (key, val) in zip(("major", "minor", "patch", "build"), tag_tuple):
        print("build.{:s}={:d}".format(key, val))


def cmp_versions(version_a, version_b, verbose=0):
    """
    Compare two version tags.
    (stolen from renovatio_selenium)

    DANGER, WILL ROBINSON:
    *build* portion is ignored.

    :param version_a: version dict 1
    :param version_b: version dict 2
    :param verbose: verbosity indicator
    :return: comparison result
    :rtype: int

    >>> a035 = {'major': 0, 'minor': 3, 'patch': 5}
    >>> b036 = {'major': 0, 'minor': 3, 'patch': 6}
    >>> c035 = {'major': 0, 'minor': 3, 'patch': 5}
    >>> cmp_versions(a035, b036)
    -1
    >>> cmp_versions(b036, a035)
    1
    >>> cmp_versions(a035, c035)
    0
    >>> x04 = {'major': 0, 'minor': 4}
    >>> cmp_versions(a035, x04)
    -1
    >>> y100 = {'major': 1, 'minor': 0, 'patch': 0}
    >>> cmp_versions(a035, y100)
    -1
    >>> cmp_versions(b036, y100)
    -1
    >>> cmp(1, 2)
    -1
    >>> cmp(2, 1)
    1
    >>> cmp_versions(git_tag_dict('17.3.22.2'), git_tag_dict('16.10.10'))
    1
    """
    if verbose > 1:
        try:
            fmt_string = "%(major)04d.%(minor)04d.%(patch)04d"
            expected = fmt_string % version_a
            actual = fmt_string % version_b
            result = cmp(actual, expected)
        except KeyError:
            result = 23
        LOG.debug("{:s} VS {:s}: {:>3d}".format(version_a, version_b, result))

    key_list = ["major", "minor", "patch"]
    cmp_value_a = 0
    cmp_value_b = 0

    i = 0
    pot = 100
    for key in reversed(key_list):
        value_a = 0
        value_b = 0

        try:
            value_a = int(version_a.get(key, 0))
        except ValueError:
            pass
        try:
            value_b = int(version_b.get(key, 0))
        except ValueError:
            pass

        if verbose > 3:
            LOG.debug(
                "[a] {:s}={:>3d} ({:>5d})".format(
                    key, value_a, value_a * pot**i
                )
            )
            LOG.debug(
                "[b] {:s}={:>3d} ({:>5d})".format(
                    key, value_b, value_b * pot**i
                )
            )

        i += 1
        cmp_value_a += value_a * pot**i
        cmp_value_b += value_b * pot**i

    i_result = cmp(cmp_value_a, cmp_value_b)
    LOG.debug("{!s} VS {!s}: {:>3d}".format(version_a, version_b, i_result))
    return i_result


def format_changelog(lines, max_version=None):
    prev_content = None
    log_map = dict()

    for line in lines:
        line = line.strip()
        m = LOG_RE.match(line)
        try:
            gdict = m.groupdict()
        except AttributeError:
            LOG.warning("#BAD: {:s}".format(line))
            continue

        content = gdict.get("msg")
        if prev_content == content:
            LOG.debug("#SKIP/DUPLICATE: {:s}".format(line))
            continue
        prev_content = content

        tag_matcher = re.match(OFFICIAL_TAG_RE, gdict.get("tag"))
        if tag_matcher is None:
            LOG.debug("#SKIP/TAG: {:s}".format(line))
            continue

        if re.match(MSG_JUNK_RE, gdict.get("msg")):
            LOG.debug("#SKIP/JUNK: {:s}".format(line))
            continue

        tag_matcher_gdict = tag_matcher.groupdict()

        for key in PORTIONS:
            val = tag_matcher_gdict.get(key, 0)
            if val is None:
                val = 0
            gdict[key] = int(val)

        gdict["ver"] = "%(major)d.%(minor)d.%(patch)d.%(build)03d" % gdict
        sort_key = "%(major)04d.%(minor)04d.%(patch)04d.%(build)04d" % gdict
        try:
            log_map[sort_key].append(gdict)
        except KeyError:
            log_map[sort_key] = [gdict]

    tags = list(reversed(sorted(log_map.keys())))

    for key in tags:
        if max_version and len(log_map[key]) > 0:
            some_tag_version = log_map[key][0]
            if cmp_versions(max_version, some_tag_version) == -1:
                LOG.error("Too recent: {!r}".format(some_tag_version["ver"]))
                continue

        print("[{:s}]".format(log_map[key][0]["tag"]))
        for log_data in log_map[key]:
            print(OUTPUT_LOG_FORMAT % log_data)
        print("")


def alter_tag(current_tag, **increment):
    """
    Alter tag values given by *increment*.

    :param current_tag: current tag dictionary
    :param increment: changeset
    :return: altered copy of *current_tag*
    :rtype: dict

    >>> git_tag_string(alter_tag(git_tag_dict("1.2.15.99")))
    '1.2.15.099'
    >>> git_tag_string(alter_tag(git_tag_dict("1.2.15.99"), build=1))
    '1.2.15.100'
    >>> alter_tag(git_tag_dict("1.2.15.99"), build=-199)
    Traceback (most recent call last):
        ...
    AssertionError
    >>> a035 = {'major': 'x', 'minor': 3, 'patch': 5}
    >>> alter_tag(a035, major=1)
    Traceback (most recent call last):
        ...
    TypeError: Can't convert 'int' object to str implicitly
    """
    next_tag = copy.copy(current_tag)

    for key in PORTIONS:
        next_tag[key] = current_tag.get(key, 0) + increment.get(key, 0)
        assert next_tag[key] >= 0

    return next_tag


if __name__ == "__main__":
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))
