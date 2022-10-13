#!/usr/bin/env python3

"""
Settings context managers

*Settings can be instanced either on it's own (write only) to accumulate changes or
from a *SettingsReader context manager, in order to read from the 'current settings'
Reading is on-demand via properties.
Writing does no work up-front, sets internal attributes with property setters, but then
the *SettingsWriter performs a sync operation, which compares 'current settings' against
those populated into the *Settings internal attributes.
For large *Settings, we don't need the *SettingsWriter overhead of pre-populating all
properties which is overkill if only one property changes.
The *SettingsReader usage in *Settings instances is 99% of the time to get access to the
QSettings instance that the reader setup.
The *SettingsWriter currently duplicates the group definition with the *SettingsReader.
This should be de-duplicated.
The *SettingsWriter needs a *SettingsReader in order to compare values, so
*SettingsReader is the one place the group should be defined.
If the *SettingsReader needs a parameter to initialise it, this should be mimick'd in
the *SettingsWriter initialiser:
- FontSettingsReader, NamedLocalCacheSettingsReader, RecipeSettingsReader

"""
