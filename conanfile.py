#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild
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
        del self.settings.compiler.libcxx

        if self.settings.os == "Windows" and \
                (self.settings.compiler != "Visual Studio" or int(str(self.settings.compiler.version)) < 14):
            raise tools.ConanException("On Windows, the opus package can only be built with the "
                                       "Visual Studio 2015 or higher.")
        if self.settings.compiler == "Visual Studio" and not self.options.shared:
            self.options.remove("fixed_point")

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def source(self):
        source_url = "https://archive.mozilla.org/pub/opus"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)
        # exclude opus_compare.c from build (it has main function)
        with tools.chdir(os.path.join(self.source_subfolder, 'win32', 'VS2015')):
            tools.replace_in_file('opus.vcxproj',
                                  '    <ClCompile Include="..\\..\\src\\opus_compare.c">\n'
                                  '      <DisableSpecificWarnings>4244;%(DisableSpecificWarnings)'
                                  '</DisableSpecificWarnings>\n'
                                  '    </ClCompile>\n', '')

    @property
    def fixed_point(self):
        if self.settings.compiler == 'Visual Studio' and not self.options.shared:
            return False
        return self.options.fixed_point

    def build_msvc(self):
        with tools.chdir(self.source_subfolder):
            pc_build = 'fixed-point' if self.fixed_point else 'floating-point'
            shutil.copy('opus.pc.in', 'opus.pc')
            tools.replace_in_file('opus.pc', '@VERSION@', self.version)
            tools.replace_in_file('opus.pc', '@PC_BUILD@', pc_build)
            tools.replace_in_file('opus.pc', '@LIBM@', '')
            tools.replace_in_file('opus.pc', '@prefix@', os.path.abspath(self.package_folder))
            tools.replace_in_file('opus.pc', '@exec_prefix@', '${prefix}')
            tools.replace_in_file('opus.pc', '@libdir@', '${exec_prefix}/lib')
            tools.replace_in_file('opus.pc', '@includedir@', '${prefix}/include')
        with tools.chdir(os.path.join(self.source_subfolder, "win32", "VS2015")):
            btype = "%s%s%s" % (self.settings.build_type, "DLL" if self.options.shared else "",
                                "_fixed" if self.fixed_point else "")
            msbuild = MSBuild(self)
            msbuild.build('opus.sln', build_type=btype, platforms={"x86": "Win32"})

    def build_configure(self):
        def chmod_plus_x(filename):
            if os.name == 'posix':
                os.chmod(filename, os.stat(filename).st_mode | 0o111)

        with tools.chdir(self.source_subfolder):
            if self.settings.os == "Macos":
                tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")
            chmod_plus_x('configure')
            if self.options.shared:
                args = ['--disable-static', '--enable-shared']
            else:
                args = ['--disable-shared', '--enable-static']
            args.append('--enable-fixed-point' if self.fixed_point else '--disable-fixed-point')
            env_build = AutoToolsBuildEnvironment(self)
            env_build.configure(args=args)
            env_build.make()
            env_build.install()

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self.build_msvc()
        else:
            self.build_configure()

    def package(self):
        self.copy("FindOPUS.cmake", ".", ".")
        self.copy("COPYING", dst="licenses", src=self.source_subfolder, keep_path=False)
        if self.settings.compiler == 'Visual Studio':
            self.copy(pattern="*", dst=os.path.join("include", "opus"),
                      src=os.path.join(self.source_subfolder, "include"), keep_path=False)
            self.copy(pattern="*.dll", dst="bin", src=self.source_subfolder, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=self.source_subfolder, keep_path=False)
            self.copy("*.pc", dst=os.path.join("lib", "pkgconfig"), src=self.source_subfolder)
            self.copy(pattern="**.pdb", dst="bin", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('m')
        self.cpp_info.includedirs.append(os.path.join('include', 'opus'))
