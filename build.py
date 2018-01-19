#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=False)

    builds = []
    for settings, options, env_vars, build_requires in builder.builds:
        if not (settings["compiler"] == "Visual Studio" and settings["compiler.version"] == "12"):
            builds.append([settings, options, env_vars, build_requires])
    builder.builds = builds

    builder.run()
