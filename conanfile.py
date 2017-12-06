#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, VisualStudioBuildEnvironment
import os


class OpusConan(ConanFile):
    name = "opus"
    version = "1.2.1"
    url = "https://opus-codec.org/"
    description = "Opus is a totally open, royalty-free, highly versatile audio codec."
    sources_dir = "sources"
    license = "https://opus-codec.org/license/"
    exports_sources = ["LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "fixed_point": [True, False]}
    default_options = "shared=False", "fPIC=True", "fixed_point=False"
    requires = ""

    def configure(self):
        del self.settings.compiler.libcxx

        if self.settings.os == "Windows":
            self.options.remove("fPIC")

        if self.settings.compiler == "Visual Studio" and not self.options.shared:
            self.options.remove("fixed_point")
            

    def source(self):
        source_url = "https://archive.mozilla.org/pub/opus"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, "sources")

    def build(self):
        if self.settings.compiler == "Visual Studio":
            env = VisualStudioBuildEnvironment(self)
            with tools.environment_append(env.vars):
                vcvars = tools.vcvars_command(self.settings)
                cd_build = "cd %s\\%s\\win32\\VS2015" % (self.conanfile_directory, self.sources_dir)
                btype = "%s%s%s" % (self.settings.build_type, "DLL" if self.options.shared else "", "_fixed" if self.options.shared and self.options.fixed_point else "")
                # Instead of using "replace" here below, would we could add the "arch" parameter, but it doesn't work when we are also
                # using the build_type parameter on conan 0.29.2 (conan bug?)
                build_command = tools.build_sln_command(self.settings, "opus.sln", build_type = btype).replace("x86", "Win32") 
                self.output.info("Build command: %s" % build_command)
                self.run("%s && %s && %s" % (vcvars, cd_build, build_command))

    def package(self):
        with tools.chdir("sources"):
            self.copy("COPYING", dst="licenses", src=self.sources_dir, keep_path=False)
            self.copy(pattern="*", dst="include", src="%s/include" % self.sources_dir, keep_path=False)
            self.copy(pattern="*.dll", dst="bin", keep_path=False)
            if self.settings.build_type == "Debug" and self.settings.compiler == "Visual Studio":
                self.copy(pattern="*pus.pdb", dst="bin", keep_path=False) # Without the *pus.pdb pattern, e.g. if we use "opus.pdb" or "opus.*" copy doesn't work on conan 0.29.2 (conan bug?)
            self.copy(pattern="*.lib", dst="lib", keep_path=False)
            self.copy(pattern="*.a", dst="lib", keep_path=False)
            self.copy(pattern="*.so*", dst="lib", keep_path=False)
            self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
