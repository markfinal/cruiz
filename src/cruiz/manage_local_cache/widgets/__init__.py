#!/usr/bin/env python3

"""
Conan manage local cache widgets
"""

from .newlocalcachewizard import NewLocalCacheWizard as NewLocalCacheWizard
from .installconfigdialog import InstallConfigDialog as InstallConfigDialog
from .movelocalcachedialog import MoveLocalCacheDialog as MoveLocalCacheDialog
from .addremotedialog import AddRemoteDialog as AddRemoteDialog
from .progressdialogs import (
    RemoveLocksDialog as RemoveLocksDialog,
    RemoveAllPackagesDialog as RemoveAllPackagesDialog,
)
from .addextraprofiledirectorydialog import (
    AddExtraProfileDirectoryDialog as AddExtraProfileDirectoryDialog,
)
from .addenvironmentdialog import AddEnvironmentDialog as AddEnvironmentDialog
from .runconancommanddialog import RunConanCommandDialog as RunConanCommandDialog
from .removeenvironmentdialog import RemoveEnvironmentDialog as RemoveEnvironmentDialog
