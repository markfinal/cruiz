#!/usr/bin/env python3

"""
Conan command parameters
"""

from io import StringIO
import pathlib
import typing

from cruiz.constants import BuildFeatureConstants

from .commonparameters import CommonParameters


# TODO: should a recipe be in here? it is quite a heavyweight Context object though
class CommandParameters(CommonParameters):
    """
    Representation of all the arguments to a command
    """

    def __init__(
        self,
        verb: str,
        worker: typing.Union[
            typing.Callable[[typing.Any, typing.Any], None],
            typing.Callable[[typing.Any, typing.Any, typing.Any], None],
        ],
    ) -> None:
        super().__init__(worker)
        self.verb = verb
        self._recipe_path: typing.Optional[
            pathlib.Path
        ] = None  # TODO: aliased with the recipe, so should we store it?
        self._cwd: typing.Optional[pathlib.Path] = None
        self._profile: typing.Optional[str] = None
        self._common_subdir: typing.Optional[pathlib.PurePosixPath] = None
        self._install_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._imports_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._source_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._build_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._package_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._test_folder: typing.Optional[pathlib.PurePosixPath] = None
        self._name: typing.Optional[str] = None
        self._version: typing.Optional[
            str
        ] = None  # TODO: these are aliased with the recipe, so should we store it?
        self._user: typing.Optional[str] = None
        self._channel: typing.Optional[str] = None
        self._options: typing.Dict[str, str] = {}
        self._force: typing.Optional[bool] = None
        self._package_reference: typing.Optional[str] = None
        self._args: typing.List[str] = []
        self._named_args: typing.Dict[str, str] = {}
        self._time_commands: typing.Optional[bool] = None

    def __str__(self) -> str:
        components = ["conan"]
        components.append(self.verb)
        if self._install_folder:
            components.extend(["-if", str(self._install_folder)])
        if self._imports_folder:
            components.extend(["-imf", str(self._imports_folder)])
        if self._source_folder:
            components.extend(["-sf", str(self._source_folder)])
        if self._build_folder:
            components.extend(["-bf", str(self._build_folder)])
        if self._package_folder:
            components.extend(["-pf", str(self._package_folder)])
        if self._test_folder:
            components.extend(["-tbf", str(self._test_folder)])
        if self._profile:
            components.extend(
                [
                    "-pr",
                    self._profile,
                ]
            )
        for key, value in self._options.items():
            components.extend(
                [
                    "-o",
                    f"{key}={value}",
                ]
            )
        if self._force:
            components.append("-f")
        if self._args:
            components.extend(self._args)
        # no named args
        if self._recipe_path:
            components.append(str(self._recipe_path))
        if self._package_reference:
            components.append(self._package_reference)
        command = " ".join(components)
        return command

    @property
    def cmd_expression(self) -> StringIO:
        """
        Get the expression valid in a CMD batch shell for this command
        """
        expression = StringIO()
        for key, value in self.added_environment.items():
            # internal envvars used in multi-process that don't immediately
            # translate to real envvars as they depend on context and also
            # poking into Conan by monkey patching
            if key.startswith("BuildFeatureConstants"):
                expression.write(f"rem {key}={value}\n")
            # avoid imposing cruiz choices on colour schemes
            if key == "CONAN_COLOR_DARK":
                expression.write(f"rem {key}={value}\n")
        # always use a child shell
        expression.write('cmd /C "')
        if self.cwd:
            expression.write(f"cd {self.cwd} && ")
        for key, value in self.added_environment.items():
            if key.startswith("BuildFeatureConstants"):
                continue
            if key == "CONAN_COLOR_DARK":
                continue
            expression.write(f"set {key}={value} && ")
        for key in self.removed_environment:
            expression.write(f"set {key}= && ")
        expression.write(str(self))
        expression.write('"')
        return expression

    @property
    def bash_expression(self) -> StringIO:
        """
        Get the expression valid in a bash shell for this command
        """
        expression = StringIO()
        for key, value in self.added_environment.items():
            # internal envvars used in multi-process that don't immediately
            # translate to real envvars as they depend on context and also
            # poking into Conan by monkey patching
            if key.startswith("BuildFeatureConstants"):
                expression.write(f"# {key}={value}\n")
            # avoid imposing cruiz choices on colour schemes
            if key == "CONAN_COLOR_DARK":
                expression.write(f"# {key}={value}\n")
        if self.cwd:
            # use a subshell
            expression.write(f"( cd {self.cwd} && ")
        for key, value in self.added_environment.items():
            if key.startswith("BuildFeatureConstants"):
                continue
            if key == "CONAN_COLOR_DARK":
                continue
            expression.write(f"{key}={value} ")
        for key in self.removed_environment:
            expression.write(f"{key}= ")
        expression.write(str(self))
        if self.cwd:
            expression.write(" )")
        return expression

    @property
    def zsh_expression(self) -> StringIO:
        """
        Get the expression valid in a zsh shell for this command
        """
        expression = StringIO()
        expression.write("setopt interactivecomments\n")
        expression.write(self.bash_expression.getvalue())
        return expression

    @property
    def recipe_path(self) -> typing.Optional[pathlib.Path]:
        """
        Get the path of the recipe used in this command.
        May be None.
        """
        return self._recipe_path

    @recipe_path.setter
    def recipe_path(self, value: typing.Optional[pathlib.Path]) -> None:
        self._recipe_path = value

    @property
    def cwd(self) -> typing.Optional[pathlib.Path]:
        """
        Get the current directory used in this command.
        May be None.
        """
        return self._cwd

    @cwd.setter
    def cwd(self, value: pathlib.Path) -> None:
        self._cwd = value

    @property
    def profile(self) -> typing.Optional[str]:
        """
        Get the profile to use in the command against this recipe.
        -pr/--profile switch
        May be None to omit
        """
        return self._profile

    @profile.setter
    def profile(self, value: typing.Optional[str]) -> None:
        self._profile = value

    @property
    def common_subdir(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the common subdirectory to apply atop of the current working directory.
        May be None to omit
        """
        return self._common_subdir

    @common_subdir.setter
    def common_subdir(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._common_subdir = value

    @property
    def install_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the install folder to use in the command against this recipe.
        -if/--install-folder switch
        May be None to omit
        """
        return self._install_folder

    @install_folder.setter
    def install_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._install_folder = value

    @property
    def imports_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the imports folder to use in the command against this recipe.
        -imf/--import-folder switch
        May be None to omit
        """
        return self._imports_folder

    @imports_folder.setter
    def imports_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._imports_folder = value

    @property
    def source_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the source folder to use in the command against this recipe.
        -sf/--source-folder switch
        May be None to omit
        """
        return self._source_folder

    @source_folder.setter
    def source_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._source_folder = value

    @property
    def build_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the build folder to use in the command against this recipe.
        -bf/--build-folder switch
        May be None to omit
        """
        return self._build_folder

    @build_folder.setter
    def build_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._build_folder = value

    @property
    def package_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the package folder to use in the command against this recipe.
        -pf/--package-folder switch
        May be None to omit
        """
        return self._package_folder

    @package_folder.setter
    def package_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._package_folder = value

    @property
    def test_folder(self) -> typing.Optional[pathlib.PurePosixPath]:
        """
        Get the test build folder to use in the command against this recipe.
        -tbf/--test-build-folder switch
        May be None to omit
        """
        return self._test_folder

    @test_folder.setter
    def test_folder(self, value: typing.Optional[pathlib.PurePosixPath]) -> None:
        self._test_folder = value

    @property
    def name(self) -> typing.Optional[str]:
        """
        Get the package name.
        May be None.
        """
        return self._name

    @name.setter
    def name(self, value: typing.Optional[str]) -> None:
        self._name = value

    @property
    def version(self) -> typing.Optional[str]:
        """
        Get the package version.
        May be None.
        """
        return self._version

    @version.setter
    def version(self, value: typing.Optional[str]) -> None:
        self._version = value

    @property
    def user(self) -> typing.Optional[str]:
        """
        Get the package user.
        May be None.
        """
        return self._user

    @user.setter
    def user(self, value: typing.Optional[str]) -> None:
        self._user = value

    @property
    def channel(self) -> typing.Optional[str]:
        """
        Get the package channel.
        May be None.
        """
        return self._channel

    @channel.setter
    def channel(self, value: typing.Optional[str]) -> None:
        self._channel = value

    @property
    def options(self) -> typing.Dict[str, str]:  # TODO: should this be immutable?
        """
        Get the recipe options.
        """
        return self._options

    def add_option(self, package_name: str, key: str, value: str) -> None:
        """
        Add an option key-value pair.
        """
        assert key not in self._options
        self._options[f"{package_name}:{key}"] = value

    @property
    def force(self) -> typing.Optional[bool]:
        """
        Get whether an option is forced.
        May be None.
        """
        return self._force

    @force.setter
    def force(self, value: typing.Optional[bool]) -> None:
        self._force = value

    @property
    def package_reference(self) -> typing.Optional[str]:
        """
        Get the package reference.
        May be None.
        """
        return self._package_reference

    def make_package_reference(self) -> None:
        """
        Make the package reference given name, version, user and channel already set.
        """
        package_reference = StringIO()
        if self._name:
            package_reference.write(f"{self._name}/")
        if self._version:
            package_reference.write(f"{self._version}@")
        if self._user:
            package_reference.write(self._user)
        if self._channel:
            package_reference.write(f"/{self._channel}")
        # in some cases, this can be empty (e.g. export-pkg)
        # but not in others (e.g. test)
        self._package_reference = package_reference.getvalue()

    @property
    def arguments(self) -> typing.List[str]:
        """
        Get the optional arguments passed as a parameter list.
        """
        return self._args

    @property
    def named_arguments(self) -> typing.Dict[str, str]:
        """
        Get the optional named arguments.
        These are not passed on the command line.
        """
        return self._named_args

    @property
    def time_commands(self) -> typing.Optional[bool]:
        """
        Get whether commands are timed.
        May be None.
        """
        return self._time_commands

    @time_commands.setter
    def time_commands(self, value: typing.Optional[bool]) -> None:
        self._time_commands = value

    def set_build_feature(self, feature: BuildFeatureConstants, value: str) -> None:
        """
        Set an optional build feature
        """
        self.added_environment[str(feature)] = value
