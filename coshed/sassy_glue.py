# !/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
import subprocess


class SassyController(object):
    __slots__ = ["log", "item_tuples"]

    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.item_tuples = []

        if args and len(args) >= 2:
            self.add_item(args[0], args[1])
        else:
            self.add_item(
                (kwargs.get("source_path"), kwargs.get("target_path"))
            )

    def add_item(self, source_path, target_path):
        try:
            self.item_tuples.append(
                (os.path.normpath(source_path), os.path.normpath(target_path))
            )
        except AttributeError as aexc:
            self.log.error(
                "Bad source/target parameter: {!r}".format(
                    (source_path, target_path)
                )
            )
            raise

    def run(self, force=False):
        for source_path, target_path in self.item_tuples:
            for source, target in self.sassy_items(
                source_path, target_path, force=force
            ):
                args = [
                    "sassc",
                    "-t",
                    "compressed",
                    "--omit-map-comment",
                    source,
                    target,
                ]
                self.log.debug("Calling {!r}".format(args))
                result = subprocess.check_call(args)
                self.log.debug(result)

    def sassy_items(self, source_path, target_path, force=False):
        for item in os.listdir(source_path):
            if item.startswith("_"):
                continue

            (trunk, ext) = os.path.splitext(item)

            if ext.lower() not in (".scss", ".sass"):
                continue

            source = os.path.normpath(os.path.join(source_path, item))
            target = os.path.normpath(
                os.path.join(target_path, "{:s}.css".format(trunk))
            )
            do_yield = False

            self.log.info(item)

            if not os.path.isfile(target):
                do_yield = True
            else:
                source_stat = os.stat(source)
                target_stat = os.stat(target)

                if source_stat.st_mtime > target_stat.st_mtime:
                    self.log.info("Need update!")
                    do_yield = True

            if do_yield:
                yield source, target


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sc = SassyController("./sassy", "./static/css")
    sc.run()
