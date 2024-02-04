#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Versioning for git projects CLI tool.
"""
from __future__ import division
from builtins import object
from past.utils import old_div
import logging
import datetime
import subprocess
import argparse
from argparse import RawDescriptionHelpFormatter

import coshed
from coshed.git_changelog_helper import git_tag_dict
from coshed.git_changelog_helper import git_current_tag
from coshed.git_changelog_helper import PORTIONS
from coshed.git_changelog_helper import git_tag_string
from coshed.git_changelog_helper import alter_tag

#: command for adding a bumped up version tag
BUMP_TAG = 'git tag -a "{next_tag}" -m "version bump"'

#: command for pushing changes to target repo
CMD_PUSH_BRANCH = "git push {target} {branch}"

#: command for pushing tags to target repo
CMD_PUSH_TAGS = "git push {target} --tags"

VERSIONING_SCHEME_CALVER = "calver"

VERSIONING_SCHEME_SEMANTIC = "semantic"

SEMANTIC_AUTO_INCREMENT_FIELD = "patch"

#: Format string for 'current' to 'next' tag bump
CURRENT_NEXT = """
        Example: current tag {current!r} will be followed by {next!r}.
"""

# Tool description
DESCRIPTION = """
calve - Versioning for git projects helper using coshed {version!s}

Automatic bumping of version tags based on current date
or existing semantic version tag.

SEMANTIC scheme: MAJOR.MINOR.PATCH[.BUILD]

CALVER scheme: YY.DD.MM[.BUILD]

        The first version bump on 2016-08-31 will yield version   16.8.31,
        the following version bump on the same day will result in 16.8.31.1
        and the next ...                                          16.8.31.2

""".format(
    version=coshed.__version__
)


def calver_next(use_log=None, **kwargs):
    """
    Generate the next version tag (calendar versioning scheme).

    Args:
        use_log: logger instance
        kwargs: optional arguments

    Returns:
        current and next tag values
    """
    if use_log is None:
        use_log = logging.getLogger(__name__)

    current_tag = git_current_tag()
    vdict = git_tag_dict(current_tag[0])

    year = int(vdict["major"])
    if (old_div(year, 1000)) < 1:
        year += 2000

    dt_prev = datetime.datetime(
        year=year, month=int(vdict["minor"]), day=int(vdict["patch"])
    )
    dt_current = datetime.datetime.now()

    try:
        bumper = int(vdict["build"])
    except TypeError:
        bumper = 0

    use_log.debug(
        "%s",
        "dt_prev={!r} dt_current={!r} bumper={!r}".format(
            dt_prev, dt_current, bumper
        ),
    )
    use_log.debug(
        "%s",
        "dt_current.date-dt_prev.date = {!r}".format(
            dt_current.date() - dt_prev.date()
        ),
    )

    dt_next = dt_current
    if dt_prev.date() < dt_current.date():
        bumper = 0

    next_tag = "{:d}.{:d}.{:d}".format(
        dt_next.year % 100, dt_next.month, dt_next.day
    )

    if bumper or dt_prev.date() == dt_current.date():
        bumper += 1
        next_tag += ".{:d}".format(bumper)

    return current_tag, next_tag


def semver_next(use_log=None, cli_args=None):
    """
    Generate the next version tag (semantic versioning scheme).

    Args:
        use_log: logger instance

    Returns:
        current and next tag values
    """
    if use_log is None:
        use_log = logging.getLogger(__name__)

    if cli_args is None:
        raise ValueError("cli_args may not be None!")

    current_tag = git_current_tag()
    vdict = git_tag_dict(current_tag[0])

    increment = dict()
    inc_keys = list()
    for portion_key in PORTIONS:
        key = "alter_{portion_key}".format(portion_key=portion_key)
        increment[portion_key] = getattr(cli_args, key)
        if increment[portion_key]:
            inc_keys.append(portion_key)

    use_log.debug("%s", "increment={!r}".format(increment))
    use_log.debug("%s", "inc_keys={!r}".format(inc_keys))

    if len(inc_keys) == 0:
        increment[SEMANTIC_AUTO_INCREMENT_FIELD] = 1
        inc_keys.append(SEMANTIC_AUTO_INCREMENT_FIELD)
    elif len(inc_keys) > 1:
        raise ValueError(
            "Only one of {!r} may be altered at once".format(PORTIONS)
        )

    inc_key = inc_keys[0]
    for key in reversed(PORTIONS):
        if key != inc_key:
            increment[key] = -vdict[key]
        else:
            break

    use_log.debug("%s", "increment={!r}".format(increment))
    use_log.debug("%s", "inc_keys={!r}".format(inc_keys))

    next_tag = git_tag_string(alter_tag(vdict, **increment))

    return current_tag, next_tag


# try adding example version bump if possible:
try:
    vdict = dict()
    for key in PORTIONS:
        alter_key = "alter_{key}".format(key=key)
        vdict[alter_key] = 0
    vdict["alter_patch"] += 1
    fake_cli_args = argparse.Namespace(**vdict)

    current_version_tag, current_next_tag = semver_next(cli_args=fake_cli_args)
    DESCRIPTION += CURRENT_NEXT.format(
        current=current_version_tag[0], next=current_next_tag
    )
except Exception as dexc:
    log = logging.getLogger(__name__)
    log.debug(dexc)


class Calve(object):
    """
    Versioning for git projects helper
    """

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.args = kwargs.get("args")
        if self.args is None:
            try:
                self._parse_cli_args()
            except Exception as exc:
                self.log.error(exc)
                self.log.warning("Error parsing CLI arguments")
                self.args = argparse.Namespace()

        if self.args.dry_run:
            self.log.info("DRY RUN ...")

    def _parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description=DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--dry-run",
            "-n",
            default=False,
            help="Dry Run",
            action="store_true",
            dest="dry_run",
        )

        group = parser.add_argument_group("Versioning Scheme")
        scheme_group = group.add_mutually_exclusive_group()

        scheme_group.add_argument(
            "--semantic",
            "-s",
            help="Semantic Versioning, default is %(default)s",
            action="store_const",
            dest="scheme",
            const=VERSIONING_SCHEME_SEMANTIC,
            default=VERSIONING_SCHEME_SEMANTIC,
        )

        scheme_group.add_argument(
            "--calver",
            "-c",
            help="Calendar Versioning, default is %(default)s",
            action="store_const",
            dest="scheme",
            const=VERSIONING_SCHEME_CALVER,
            default=VERSIONING_SCHEME_SEMANTIC,
        )

        publish = parser.add_argument_group("Publish Options")

        publish.add_argument(
            "--lazy-bum",
            "-l",
            default=False,
            help="Push changes and tag after version bumping",
            action="store_true",
            dest="lazy_bum",
        )

        publish.add_argument(
            "--lazy-devpi",
            "-p",
            default=False,
            help="Upload using devpi after version bumping",
            action="store_true",
            dest="lazy_devpi",
        )

        publish.add_argument(
            "--target",
            "-t",
            metavar="GIT_ORIGIN",
            help="git target. default: %(default)s",
            default="origin",
            dest="git_target",
        )

        publish.add_argument(
            "--branch",
            "-b",
            metavar="GIT_BRANCH",
            help="git branch. default: %(default)s",
            default="master",
            dest="git_branch",
        )

        alter = parser.add_argument_group("Tag altering")
        alter.add_argument(
            "--major",
            "--aa",
            dest="alter_major",
            const=1,
            action="store_const",
            default=0,
            help="increment MAJOR version portion",
        )
        alter.add_argument(
            "--minor",
            "--ai",
            dest="alter_minor",
            const=1,
            action="store_const",
            default=0,
            help="increment MINOR version portion",
        )
        alter.add_argument(
            "--patch",
            "--ap",
            dest="alter_patch",
            const=1,
            action="store_const",
            default=0,
            help="increment PATCH version portion",
        )
        alter.add_argument(
            "--build",
            "--ab",
            dest="alter_build",
            const=1,
            action="store_const",
            default=0,
            help="increment BUILD version portion",
        )

        self.args = parser.parse_args()

    def main(self):
        """
        Main Loop
        """
        if self.args.scheme == VERSIONING_SCHEME_CALVER:
            bump_func = calver_next
        elif self.args.scheme == VERSIONING_SCHEME_SEMANTIC:
            bump_func = semver_next
        else:
            raise NotImplementedError(self.args.scheme)

        current_tag, next_tag = bump_func(use_log=self.log, cli_args=self.args)

        self.log.info(
            "Bumping tag from {current_tag} to {next_tag}".format(
                current_tag=current_tag[0], next_tag=next_tag
            )
        )

        assert current_tag[0] != next_tag
        self._bump(next_tag=next_tag)

        if self.args.lazy_bum:
            self.log.warning("You lazy bum!")
            self._publish()

        if self.args.lazy_devpi:
            self.log.warning("You lazy bum!")
            self._devpi_upload()

    def _call(self, cmd):
        """
        Simple execution of arbitrary commands.

        Args:
            cmd: command

        Returns:
            return code
        """
        self.log.debug(cmd)
        return subprocess.call(cmd, shell=True)

    def _bump(self, next_tag):
        """
        Create a bumped up git tag

        Args:
            next_tag: new tag

        Returns:
            return code
        """
        cmd = BUMP_TAG.format(next_tag=next_tag)

        if self.args.dry_run:
            self.log.info("%s", "WOULD execute {!r}".format(cmd))
            return

        return self._call(cmd)

    def _publish(self):
        """
        Push changes and tag to target repository.

        Returns:
            return codes
        """
        params = {
            "target": self.args.git_target,
            "branch": self.args.git_branch,
        }
        rcs = []

        for cmd_fmt in [CMD_PUSH_BRANCH, CMD_PUSH_TAGS]:
            cmd = cmd_fmt.format(**params)

            if self.args.dry_run:
                self.log.info("%s", "WOULD execute {!r}".format(cmd))
                continue

            rcs.append(self._call(cmd))

        return rcs

    def _devpi_upload(self):
        """
        Upload package using devpi

        Returns:
            return codes
        """
        rcs = []

        cmd = "devpi upload"

        if self.args.dry_run:
            self.log.info("%s", "WOULD execute {!r}".format(cmd))
            return

        rcs.append(self._call(cmd))

        return rcs


def cli_stub():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)-15s %(levelname)8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cli = Calve()
    cli.main()
