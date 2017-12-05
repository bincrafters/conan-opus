#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class OpusConan(ConanFile):
    name = "opus"
    version = "1.2.1"
    url = "https://opus-codec.org/"
    description = "Opus is a totally open, royalty-free, highly versatile audio codec."
    license = "https://opus-codec.org/license/"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False"
    requires = ""

    def configure(self):
        del self.settings.compiler.libcxx

        if self.settings.os == "Windows":
            self.options.remove("fPIC")
            

    def source(self):
        source_url = "https://archive.mozilla.org/pub/opus"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, "sources")

    def build(self):

        self.output.info("build here")


    def package(self):
        with tools.chdir("sources"):
            self.copy(pattern="LICENSE")
            self.copy(pattern="*", dst="include", src="include")
            self.copy(pattern="*.dll", dst="bin", src="bin", keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.a", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.so*", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.dylib", dst="lib", src="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
