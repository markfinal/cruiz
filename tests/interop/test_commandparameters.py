"""Tests for command parameters."""

import os
import pathlib
import typing

import cruizlib.globals
from cruizlib.constants import BuildFeatureConstants
from cruizlib.interop.commandparameters import CommandParameters


MOCKED_VERB = "mocked_verb"


# pylint: disable=unused-argument
def _mocked_worker(first: typing.Any, second: typing.Any) -> None:
    pass


def test_cmdparams_profile() -> None:
    """Set the Conan profile."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.profile = "my_profile"
    assert cp.to_args()[-2] == "-pr"
    assert cp.to_args()[-1] == "my_profile"


def test_cmdparams_custom_args() -> None:
    """Add custom arguments."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    args = cp.arguments
    args.append("--update")
    assert cp.to_args()[-1] == "--update"


def test_cmdparams_install_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan install folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.install_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-if"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_imports_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan imports folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.imports_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-imf"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_source_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan source folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.source_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-sf"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_build_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan build folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.build_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-bf"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_package_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan package folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.package_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-pf"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_test_folder(tmp_path: pathlib.Path) -> None:
    """Set the Conan test folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.test_build_folder = tmp_path
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-2] == "-tbf"
        assert cp.to_args()[-1] == os.fspath(tmp_path)
    else:
        assert len(cp.to_args()) == 1


def test_cmdparams_options() -> None:
    """Set the Conan recipe options."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        cp.add_option(None, "global_option", "go_value")
        cp.add_option("my_package", "package_option", "po_value")
        assert len(cp.options) == 2
        assert cp.to_args()[-2] == "-o"
        assert cp.to_args()[-1] == "my_package:package_option=po_value"
        assert cp.to_args()[-4] == "-o"
        assert cp.to_args()[-3] == "global_option=go_value"
    else:
        # options always have a package prefix now
        cp.add_option("my_package", "package_option", "po_value")
        assert len(cp.options) == 1
        assert cp.to_args()[-2] == "-o"
        assert cp.to_args()[-1] == "my_package/*:package_option=po_value"


def test_cmdparams_force() -> None:
    """Set the Conan force option."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.force = True
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-1] == "-f"
    else:
        assert cp.to_args()[-1] == "-c"


def test_cmdparams_recipe_path(tmp_path: pathlib.Path) -> None:
    """Set the Conan recipe path."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.recipe_path = tmp_path
    assert cp.to_args()[-1] == os.fspath(tmp_path)


def test_cmdparams_package_reference() -> None:
    """Set the Conan package_reference."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.name = "my_package"
    cp.version = "1.2.3"
    cp.user = "user"
    cp.channel = "channel"
    cp.make_package_reference()
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert cp.to_args()[-1] == "my_package/1.2.3@user/channel"
    else:
        cp.v2_need_reference = True
        assert cp.to_args()[-1] == "my_package/1.2.3@user/channel"
        cp.v2_need_reference = False
        assert cp.to_args()[-8] == "--name"
        assert cp.to_args()[-7] == "my_package"
        assert cp.to_args()[-6] == "--version"
        assert cp.to_args()[-5] == "1.2.3"
        assert cp.to_args()[-4] == "--user"
        assert cp.to_args()[-3] == "user"
        assert cp.to_args()[-2] == "--channel"
        assert cp.to_args()[-1] == "channel"


def test_cmdparams_cmd_expression(tmp_path: pathlib.Path) -> None:
    """Expressions available in CMD evaluation."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.set_build_feature(BuildFeatureConstants.CMAKEFINDDEBUGMODE, "ON")
    cp.added_environment.update({"MY_ENVVAR": "ENVVAR_VALUE", "CONAN_COLOR_DARK": "1"})
    cp.removed_environment.append("MY_REMOVED_ENVVAR")
    cp.cwd = tmp_path
    cp.arguments.append("")  # intentionally empty
    cp.add_option("*", "shared", "True")
    expr = cp.cmd_expression.getvalue()
    assert "rem BuildFeatureConstants.CMAKEFINDDEBUGMODE=ON" in expr
    assert "set MY_ENVVAR=ENVVAR_VALUE &&" in expr
    assert "rem CONAN_COLOR_DARK=1" in expr
    assert f"cd {tmp_path} &&" in expr
    assert "set MY_REMOVED_ENVVAR= &&" in expr
    assert '""' in expr
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert '-o "*:shared=True"' in expr
    else:
        assert '-o "*/*:shared=True"' in expr


def test_cmdparams_bash_expression(tmp_path: pathlib.Path) -> None:
    """Expressions available in bash evaluation."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.set_build_feature(BuildFeatureConstants.CMAKEFINDDEBUGMODE, "ON")
    cp.added_environment.update({"MY_ENVVAR": "ENVVAR_VALUE", "CONAN_COLOR_DARK": "1"})
    cp.removed_environment.append("MY_REMOVED_ENVVAR")
    cp.cwd = tmp_path
    cp.arguments.append("")  # intentionally empty
    cp.add_option("*", "shared", "True")
    expr = cp.bash_expression.getvalue()
    assert "# BuildFeatureConstants.CMAKEFINDDEBUGMODE=ON" in expr
    assert "MY_ENVVAR=ENVVAR_VALUE " in expr
    assert "# CONAN_COLOR_DARK=1" in expr
    assert f"cd {tmp_path} &&" in expr
    assert "MY_REMOVED_ENVVAR= " in expr
    assert '""' in expr
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert '-o "*:shared=True"' in expr
    else:
        assert '-o "*/*:shared=True"' in expr


def test_cmdparams_zsh_expression(tmp_path: pathlib.Path) -> None:
    """Expressions available in zsh evaluation."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.set_build_feature(BuildFeatureConstants.CMAKEFINDDEBUGMODE, "ON")
    cp.added_environment.update({"MY_ENVVAR": "ENVVAR_VALUE", "CONAN_COLOR_DARK": "1"})
    cp.removed_environment.append("MY_REMOVED_ENVVAR")
    cp.cwd = tmp_path
    cp.arguments.append("")  # intentionally empty
    cp.add_option("*", "shared", "True")
    expr = cp.zsh_expression.getvalue()
    assert "# BuildFeatureConstants.CMAKEFINDDEBUGMODE=ON" in expr
    assert "MY_ENVVAR=ENVVAR_VALUE " in expr
    assert "# CONAN_COLOR_DARK=1" in expr
    assert f"cd {tmp_path} &&" in expr
    assert "MY_REMOVED_ENVVAR= " in expr
    assert '""' in expr
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        assert '-o "*:shared=True"' in expr
    else:
        assert '-o "*/*:shared=True"' in expr
    assert expr.startswith("setopt interactivecomments")


def test_cmdparams_common_subdir(tmp_path: pathlib.Path) -> None:
    """Set the Conan common subdirectory."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.common_subdir = tmp_path
    assert cp.common_subdir == tmp_path


def test_cmdparams_check_namedargs(tmp_path: pathlib.Path) -> None:
    """Check passed named arguments."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.named_arguments["tmp_path"] = os.fspath(tmp_path)
    assert "tmp_path" in cp.named_arguments
    assert cp.named_arguments["tmp_path"] == os.fspath(tmp_path)


def test_cmdparams_time_commands() -> None:
    """Enable time commands."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.time_commands = True
    assert cp.time_commands


def test_cmdparams_v2_omit_test_folder() -> None:
    """Conan2 omit test folder."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.v2_omit_test_folder = True
    assert cp.v2_omit_test_folder
    if cruizlib.globals.CONAN_MAJOR_VERSION == 1:
        pass
    else:
        assert not cp.to_args()[-1]
        assert cp.to_args()[-2] == "-tf"


def test_cmdparams_v2_need_ref() -> None:
    """Conan2 need reference."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.v2_need_reference = True
    assert cp.v2_need_reference


def test_cmdparams_extra_options() -> None:
    """Adding extra options."""
    cp = CommandParameters(MOCKED_VERB, _mocked_worker)
    cp.extra_options = "extra_options"
    assert cp.extra_options == "extra_options"
