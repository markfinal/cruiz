#!/usr/bin/env python3

"""
Conan manage local cache widgets
"""

from .addenvironmentdialog import AddEnvironmentDialog as AddEnvironmentDialog
from .addextraprofiledirectorydialog import (
    AddExtraProfileDirectoryDialog as AddExtraProfileDirectoryDialog,
)
from .addremotedialog import AddRemoteDialog as AddRemoteDialog
from .installconfigdialog import InstallConfigDialog as InstallConfigDialog
from .movelocalcachedialog import MoveLocalCacheDialog as MoveLocalCacheDialog
from .newlocalcachewizard import NewLocalCacheWizard as NewLocalCacheWizard
from .progressdialogs import (
    RemoveAllPackagesDialog as RemoveAllPackagesDialog,
    RemoveLocksDialog as RemoveLocksDialog,
)
from .removeenvironmentdialog import RemoveEnvironmentDialog as RemoveEnvironmentDialog
from .runconancommanddialog import RunConanCommandDialog as RunConanCommandDialog
