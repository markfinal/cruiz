# Welcome to cruiz

cruiz stands for Conan Recipe User Interface.

At this time, only Conan 1.x is supported in versions 1.3.x.
However, there are alpha releases of Cruiz 1.4.0 that dual support Conan 2.x (from v2.0.7), reusing most of the existing UI.

## Goals
The goals of cruiz are as follows:

* Responsive UI
> multiprocessing is used for each Conan command to separate UI and asynchronous workers.

* Managing local caches
> Local caches are named, associated with recipes, and deals with Conan environment variables.

* Visualisation of dependencies
> Visualisation of the package dependency graph using GraphViz and SVG.

* Ease Conan learning curve
> Reduce the learning curve on Conan specifics.

* Alternative remote package inspection
> Something different to Artifactory's web interface but on the client side. Improvements such as syntax highlighted file viewing.

## Main menu
### File menu
* `Open...` to open a recipe into a tab
* `Recent recipes` to view a list of previously opened recipes
* `Quit`
### Edit menu
* `Preferences...` to open the preferences dialog
* `Manage local caches...` to open the local cache management dialog
### View menu
* `Conan remote browser` to toggle the remote browser dock
### Help menu
* `About cruiz...` to view version information about cruiz and the Python ecosystem running
* `About Qt...` to show the standard Qt version dialog
* `Icon licenses...` to show the licenses for icons used

## Recipes are first class citizens
Conan recipe files (conanfile.py/conanfile.txt) are the primary files that cruiz will open.

Use `File->Open...` to open a recipe into the UI. A wizard will be shown to guide the loading process for any recipe unknown to cruiz. Version agnostic recipes are supported, and the associated conandata.yml is parsed to determine the versions available.

Multiple recipes can be loaded, each into their own tab.

Commands are run on the recipe with focus. There is a choice in the UI of using the following to invoke commands:

1. keyboard shortcuts, defined in preferences
2. menu options from the Commands menu in each recipe tab
3. toolbar buttons across the top of each recipe tab

## Manage local caches
Conan supports local caches in different locations. Working with different projects may require a different local cache for each. This can be done with environment variables.

cruiz offers a mechanism to associate a recipe file with a named local cache. This binding is kept in preferences. The binding can be changed if you need to move recipe output to a different cache.

Use `Edit->Manage local caches...` to manage the named local caches. A wizard will guide you through the steps when creating a new named local cache.

## Remote browser
The Artifactory web UI and the Conan CLI are the common ways to browse and search for packages on a remote of an Artifactory server. cruiz offers an alternative viewer, with an interactive package reference search leading to recipe revisions, package_ids, package revisions, and finally a browser over package tarballs themselves. Revisions are only shown when that feature is enabled.

The remote browser dock visibility can been toggled via the `View->Conan remote browser` menu option.

### Binary browser
There are a few differences being able to view the package binary files in cruiz compared to the Artifactory web UI:

* cruiz needs to download the `conan_package.tgz` so if these are large, it may take some time
* cruiz identifies text files, symbolic links, and binary files
* cruiz can syntax highlight text files if their context can be correctly determined from their extension
* cruiz allows hiving off the `conan_package.tgz` to your local disk for additional processing

## Preferences
Many features of cruiz can be configured via the preferences. Features are logically grouped to make finding what you want easier. Most settings can be applied while the dialog remains open; a few require restarting the application.

Use `Edit->Preferences...` to open the preferences dialog.

## Recipe tabs
Each recipe loaded into cruiz is displayed as a tab in the UI. Each tab widget is split into several sections by default:

1. the output panes
2. menu
3. toolbars along the top
4. a dock to the left, showing the dependencies of the recipe and a visualisation of them
5. a dock to the right, split between configuration of the recipe and local workflow options
6. a dock to the bottom, split between a history of Conan commands run on the recipe, and the Conan log stream

### Output Panes
The central widget to each recipe tab is the output area, where the output from commands run is displayed.

Features of this pane
* Output is colourised
* Output and error streams can be combined or split into separate panes; set in preferences.
* Text is searchable. See the context menu over the pane.
* Text is clearable. This can be performed manually via the context menu, or automatically upon each new command run in the preerences.
* Pane output can be pinned to a separate tab (single level of pinning only) via the context menu; this may be useful for comparing output on multiple runs

### Menus
#### Recipe menu
This menu offers options to interact with the recipe, and the local cache it is associated with.

* `Open recipe in editor...` uses the configured editor to view the recipe file
* `Open recipe folder...` opens the file system folder containing the recipe file
* `Copy recipe folder to clipboard`
* `Open another version of this recipe...` opens a wizard to open a new recipe tab for a different version for version agnostic recipes
* `Manage associated local cache...` opens the local cache management dialog for the cache associated with this recipe
* `Reload` reloads the recipe from disk, and updates the UI
* `Close`

#### Commands menu
This menu offers all of the Conan (and other) commands that are on the toolbars.

* `Create package in local cache` runs `conan create`
* `Create package in local cache with latest dependencies` runs `conan create -u`
* Local workflow
    * `Download dependencies and configure` runs `conan install`
    * `Download latest dependencies and configure` runs `conan install -u`
    * `Import files from dependents` runs `conan imports`
    * `Get source code` runs `conan source`
    * `Build source` runs `conan build`
    * `Make local package` runs `conan package`
    * `Export package to local cache` runs `conan export-pkg`
    * `Test package in local cache` runs `conan test`
    * CMake
        * `Run CMake build tool` runs `cmake --build` in the build folder
        * `Run CMake build tool (verbose)` runs `cmake --build` in verbose mode in the build folder
        * `Delete CMake cache` deletes the `CMakeCache.txt` file in the build folder
* `Remove package from local cache` runs `conan remove -f`
* `Cancel running command` will stop any running command in cruiz.

### Toolbars
#### Profile
A combobox offering all of the profiles in the associated local cache.
#### Cores
A spinbox offering a way to change the number of cores that Conan commands will use.
#### Commands
Toolbar icons for each Conan and other commands that can be executed on the recipe. Tooltips contain the exact command to be executed on the command line, and will update with changes to the configuration of the recipe.
#### CMake
Checkboxes to enable verbose CMake output and enabling CMake find debug mode. These are to avoid needing to modify any build scripts on disk.
#### Compiler caching
cruiz is aware of several compiler caching technologies:

* ccache
* sccache
* buildcache

CMake based builds should integrate with any of these.
Autotools based builds can be configured to add extra command line flags to integrate.

### Dependencies dock
This is a representation of a Conan lock file for the recipe in its selected configuration.
This displays a flat list of the dependencies found and a graphical representation, if graphviz has been configured. Double clicking on the small visualisation opens a separate dialog showing it full size, with an option to save as an SVG.

### Configuration dock
Split into three sections, it shows:

1. the package_id computed from the lockfile
2. all of the options in the recipe, showing all possible values to choose from for each
3. the package reference namespace, @user/channel, to use for the recipe

Modifying any input data to the lockfile generation will recompute the package_id.

### Local workflow dock
Split into several sections, this allows the definition of paths used in Conan local workflows.

### Conan command dock
Whenever a command is executed on a recipe, it is recorded in the command log. This is intended both as a learning mechanism by seeing what changes by modifying a recipe's configuration, but also as a reproducible mechanism as right clicking over a command allows exporting it to different shells.

### Conan log dock
Running Conan commands captures logging from Conan itself, which is displayed in this dock. This is for diagnostic purposes only really.
