#!/usr/bin/env python3

"""
Any monkeypatching required
"""

import logging
import os
import pathlib
import typing

import conans

from cruiz.constants import BuildFeatureConstants


def _monkey_patch_logger() -> None:
    # Monkey patched version of conans.util.log.configure_logger
    # that does not always remove handlers, keeps the qt handler
    def qt_configure_logger(
        logging_level: int = logging.CRITICAL, logging_file: typing.Optional[str] = None
    ) -> logging.Logger:
        # pylint: disable=unused-argument
        # pylint: disable=import-outside-toplevel
        import cruiz.workers.utils.qtlogger

        logger = logging.getLogger("conans")
        qt_logger = cruiz.workers.utils.qtlogger.QtLogger()
        if qt_logger in logger.handlers:
            return logger
        for hand in logger.handlers:
            logger.removeHandler(hand)
        logger.addHandler(qt_logger)
        logger.setLevel(logging_level)
        logger.propagate = False
        return logger

    conans.util.log.configure_logger = qt_configure_logger


try:
    # conan < 1.34.0
    original_cmake_build_helper_configure = (
        conans.client.build.cmake.CMakeBuildHelper.configure
    )
except AttributeError:
    try:
        original_cmake_build_helper_configure = (
            conans.client.build.cmake.CMake.configure
        )
    except AttributeError:
        print("CONAN 2: Fix up CMake configure monkey patch")


def _monkey_patch_cmake_helper() -> None:
    def new_configure(
        self: typing.Any,
        args: typing.Any = None,
        defs: typing.Any = None,
        source_dir: typing.Any = None,
        build_dir: typing.Any = None,
        source_folder: typing.Any = None,
        build_folder: typing.Any = None,
        cache_build_folder: typing.Any = None,
        pkg_config_paths: typing.Any = None,
    ) -> None:
        # CMake find debug support
        if str(BuildFeatureConstants.CMAKEFINDDEBUGMODE) in os.environ:
            defs = defs or {}
            defs["CMAKE_FIND_DEBUG_MODE"] = "TRUE"

        # CMake verbose support
        if str(BuildFeatureConstants.CMAKEVERBOSEMODE) in os.environ:
            defs = defs or {}
            defs["CMAKE_VERBOSE_MAKEFILE"] = "TRUE"

        # CMake compiler cache support
        cache_executable = os.environ.get(str(BuildFeatureConstants.CCACHEEXECUTABLE))
        if cache_executable is None:
            cache_executable = os.environ.get(
                str(BuildFeatureConstants.SCCACHEEXECUTABLE)
            )
        if cache_executable is None:
            cache_executable = os.environ.get(
                str(BuildFeatureConstants.BUILDCACHEEXECUTABLE)
            )
        if cache_executable:
            defs = defs or {}
            defs["CMAKE_C_COMPILER_LAUNCHER"] = cache_executable
            defs["CMAKE_CXX_COMPILER_LAUNCHER"] = cache_executable

        # now execute the old function
        original_cmake_build_helper_configure(
            self,
            args,
            defs,
            source_dir,
            build_dir,
            source_folder,
            build_folder,
            cache_build_folder,
            pkg_config_paths,
        )

    try:
        # conan < 1.34.0
        conans.client.build.cmake.CMakeBuildHelper.configure = new_configure
    except AttributeError:
        try:
            conans.client.build.cmake.CMake.configure = new_configure
        except AttributeError:
            print("CONAN 2: Fix up CMake monkey patch")


try:
    original_autotools_build_helper_configure = (
        conans.client.build.autotools_environment.AutoToolsBuildEnvironment.configure
    )

    original_autotools_build_helper_make = (
        conans.client.build.autotools_environment.AutoToolsBuildEnvironment.make
    )
except AttributeError:
    print("CONAN 2: Fix up Autotools monkey patch")


def _monkey_patch_autotools_helper() -> None:
    def new_configure(
        self: typing.Any,
        configure_dir: typing.Any = None,
        args: typing.Any = None,
        build: typing.Any = None,
        host: typing.Any = None,
        target: typing.Any = None,
        pkg_config_paths: typing.Any = None,
        vars: typing.Any = None,
        use_default_install_dirs: typing.Any = True,
    ) -> None:
        args = args or []
        cache_executable = os.environ.get(str(BuildFeatureConstants.CCACHEEXECUTABLE))
        if cache_executable is not None:
            args.extend(
                os.environ.get(
                    str(BuildFeatureConstants.CCACHEAUTOTOOLSCONFIGARGS), ""
                ).split(" ")
            )
        else:
            cache_executable = os.environ.get(
                str(BuildFeatureConstants.SCCACHEEXECUTABLE)
            )
            if cache_executable is not None:
                args.extend(
                    os.environ.get(
                        str(BuildFeatureConstants.SCCACHEAUTOTOOLSCONFIGARGS), ""
                    ).split(" ")
                )
            else:
                cache_executable = os.environ.get(
                    str(BuildFeatureConstants.BUILDCACHEEXECUTABLE)
                )
                if cache_executable is not None:
                    args.extend(
                        os.environ.get(
                            str(BuildFeatureConstants.BUILDCACHEAUTOTOOLSCONFIGARGS), ""
                        ).split(" ")
                    )
        if cache_executable:
            # if using autotools, GCC is almost implied
            # on macOSX, gcc/g++ do exist and do report being apple clang
            vars = vars or {}
            vars["CC"] = f"{cache_executable} gcc"
            vars["CXX"] = f"{cache_executable} g++"
            vars["PATH"] = [os.fspath(pathlib.Path(cache_executable).parent)]

        # now execute the old function
        original_autotools_build_helper_configure(
            self,
            configure_dir,
            args,
            build,
            host,
            target,
            pkg_config_paths,
            vars,
            use_default_install_dirs,
        )

    try:
        conans.client.build.autotools_environment.AutoToolsBuildEnvironment.configure = (  # noqa: E501
            new_configure
        )
    except AttributeError:
        print("CONAN 2: Fix up Autotools monkey patch")

    def new_make(
        self: typing.Any,
        args: str = "",
        make_program: typing.Optional[str] = None,
        target: typing.Optional[str] = None,
        vars: typing.Any = None,
    ) -> None:
        cache_executable = os.environ.get(str(BuildFeatureConstants.CCACHEEXECUTABLE))
        if cache_executable is None:
            cache_executable = os.environ.get(
                str(BuildFeatureConstants.SCCACHEEXECUTABLE)
            )
        if cache_executable is None:
            cache_executable = os.environ.get(
                str(BuildFeatureConstants.BUILDCACHEEXECUTABLE)
            )
        if cache_executable:
            vars = vars or {}
            vars["CC"] = f"{cache_executable} gcc"
            vars["CXX"] = f"{cache_executable} g++"
            vars["PATH"] = [os.fspath(pathlib.Path(cache_executable).parent)]

        # now execute the old function
        original_autotools_build_helper_make(self, args, make_program, target, vars)

    try:
        conans.client.build.autotools_environment.AutoToolsBuildEnvironment.make = (
            new_make
        )
    except AttributeError:
        print("CONAN 2: Fix up Autotools monkey patch")


def _do_monkey_patching() -> None:
    _monkey_patch_logger()
    _monkey_patch_cmake_helper()
    _monkey_patch_autotools_helper()


_do_monkey_patching()
