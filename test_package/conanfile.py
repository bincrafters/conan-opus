#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools, RunEnvironment
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
            pcm_path = os.path.join(self.source_folder, "test.pcm")
            bin_path = os.path.join("bin", "test_package")
            if self.settings.os == "Windows":
                self.run("%s %s out.pcm" % (bin_path, pcm_path))
            elif self.settings.os == "Macos":
                self.run("DYLD_LIBRARY_PATH=%s %s %s out.pcm" % (os.environ.get('DYLD_LIBRARY_PATH', ''), bin_path, pcm_path))
            else:
                self.run("LD_LIBRARY_PATH=%s %s %s out.pcm" % (os.environ.get('LD_LIBRARY_PATH', ''), bin_path, pcm_path))
