#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, VisualStudioBuildEnvironment, AutoToolsBuildEnvironment
import os
import shutil


class OpusConan(ConanFile):
    name = "opus"
    version = "1.2.1"
    url = "https://opus-codec.org/"
    description = "Opus is a totally open, royalty-free, highly versatile audio codec."

    license = "BSD 3-Clause"
    homepage = "https://opus-codec.org"
    exports = ["LICENSE.md"]
    exports_sources = ["FindOPUS.cmake"]

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "fixed_point": [True, False]}
    default_options = "shared=False", "fPIC=True", "fixed_point=False"

    # Custom attributes for Bincrafters recipe conventions
    source_subfolder = "sources"
    install_subfolder = "install"

    def configure(self):

        if self.settings.os == "Windows" and (self.settings.compiler != "Visual Studio" or int(self.settings.compiler.version.__str__()) < 14):
            raise tools.ConanException("On Windows, the opus package can only be built with the Visual Studio 2015 or higher.")

        del self.settings.compiler.libcxx

        if self.settings.os == "Windows":
            self.options.remove("fPIC")

        if self.settings.compiler == "Visual Studio" and not self.options.shared:
            self.options.remove("fixed_point")

    def source(self):
        source_url = "https://archive.mozilla.org/pub/opus"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(self.source_subfolder):
                pc_build = 'fixed-point' if self.options.shared and self.options.fixed_point else 'floating-point'
                shutil.copy('opus.pc.in', 'opus.pc')
                tools.replace_in_file('opus.pc', '@VERSION@', self.version)
                tools.replace_in_file('opus.pc', '@PC_BUILD@', pc_build)
            env = VisualStudioBuildEnvironment(self)
            with tools.environment_append(env.vars):
                with tools.chdir(os.path.join(self.source_subfolder, "win32", "VS2015")):
                    vcvars = tools.vcvars_command(self.settings)
                    btype = "%s%s%s" % (self.settings.build_type, "DLL" if self.options.shared else "", "_fixed" if self.options.shared and self.options.fixed_point else "")
                    # Instead of using "replace" here below, would we could add the "arch" parameter, but it doesn't work when we are also
                    # using the build_type parameter on conan 0.29.2 (conan bug?)
                    build_command = tools.build_sln_command(self.settings, "opus.sln", build_type = btype).replace("x86", "Win32")
                    self.output.info("Build command: %s" % build_command)
                    self.run("%s && %s" % (vcvars, build_command))
        else:
            env = AutoToolsBuildEnvironment(self)

            if self.settings.os != "Windows":
                env.fpic = self.options.fPIC

            with tools.environment_append(env.vars):

                with tools.chdir(self.source_subfolder):
                    if self.settings.os == "Macos":
                        tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")

                    if self.settings.os == "Windows":
                        tools.run_in_windows_bash(self, "./configure%s" % (" --enable-fixed-point" if self.options.fixed_point else ""))
                        tools.run_in_windows_bash(self, "make")
                    else:
                        configure_options = " --prefix=%s" % os.path.join(self.build_folder, self.install_subfolder)
                        if self.options.fixed_point:
                            configure_options += " --enable-fixed-point"
                        if self.options.shared:
                            configure_options += " --disable-static --enable-shared"
                        else:
                            configure_options += " --disable-shared --enable-static"
                        self.run("chmod +x configure")
                        self.run("./configure%s" % configure_options)
                        self.run("make")
                        self.run("make install")

    def package(self):
        if self.settings.os == "Windows":
            base_folder = self.source_subfolder
        else:
            base_folder = self.install_subfolder
        self.copy("FindOPUS.cmake", ".", ".")
        self.copy("COPYING", dst="licenses", src=self.source_subfolder, keep_path=False)
        self.copy(pattern="*", dst="include", src=os.path.join(base_folder, "include"), keep_path=False)
        self.copy(pattern="*.dll", dst="bin", src=os.path.join(base_folder), keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src=os.path.join(base_folder), keep_path=False)
        self.copy(pattern="*.a", dst="lib", src=os.path.join(base_folder, "lib"), keep_path=False)
        self.copy(pattern="*.so*", dst="lib", src=os.path.join(base_folder, "lib"), keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", src=os.path.join(base_folder, "lib"), keep_path=False)
        self.copy("*.*", dst="lib/pkgconfig", src=os.path.join(base_folder, "lib", "pkgconfig"))
        if self.settings.build_type == "Debug" and self.settings.compiler == "Visual Studio":
            # Without the *pus.pdb pattern, e.g. if we use "opus.pdb" or "opus.*" copy doesn't work on conan 0.29.2 (conan bug?)
            self.copy(pattern="*pus.pdb", dst="bin", keep_path=False)
        if self.settings.compiler == 'Visual Studio':
            self.copy("*.pc", dst=os.path.join("lib, pkgconfig"), src=base_folder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
