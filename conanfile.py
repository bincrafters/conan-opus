#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild, CMake
import os
import shutil


class OpusConan(ConanFile):
    name = "opus"
    version = "1.3.1"
    url = "https://opus-codec.org/"
    description = "Opus is a totally open, royalty-free, highly versatile audio codec."
    author = "Bincrafters <bincrafters@gmail.com>"
    topics = ("conan", "opus", "audio", "decoder", "decoding", "multimedia", "sound")

    license = "BSD-3-Clause"
    homepage = "https://opus-codec.org"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt","FindOPUS.cmake","opus_buildtype.cmake"]

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "fixed_point": [True, False]}
    default_options = {'shared': False, 'fPIC': True, 'fixed_point': False}

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "sources"
    _install_subfolder = "install"

    def configure(self):
        del self.settings.compiler.libcxx

        if self.settings.os == "Windows" and \
                (self.settings.compiler != "Visual Studio" or int(str(self.settings.compiler.version)) < 14):
            raise tools.ConanException("On Windows, the opus package can only be built with the "
                                       "Visual Studio 2015 or higher.")

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")


    def source(self):
        source_url = "https://archive.mozilla.org/pub/opus"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, self.version),
                  sha256="65b58e1e25b2a114157014736a3d9dfeaad8d41be1c8179866f144a2fb44ff9d")
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        # They forgot to package that file into the tarball for 1.3.1
        # See https://github.com/xiph/opus/issues/129
        os.rename("opus_buildtype.cmake", os.path.join(self._source_subfolder , "opus_buildtype.cmake"))

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["OPUS_FIXED_POINT"] = self.options.fixed_point
        cmake.configure(source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("FindOPUS.cmake", ".", ".")
        self.copy("COPYING", dst="licenses", src=self._source_subfolder, keep_path=False)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('m')
        self.cpp_info.includedirs.append(os.path.join('include', 'opus'))
