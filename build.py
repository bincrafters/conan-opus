#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=True)

    items = []
    for item in builder.items:
        if not (item.settings["compiler"] == "Visual Studio" and item.settings["compiler.version"] == "12"):
            items.append(item)
    builder.items = items

    builder.run()
