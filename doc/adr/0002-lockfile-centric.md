# 2. Lockfile centric

Date: 2025-01-02

## Status

Proposed

## Context

Current package configuration features are not sufficient for all types of build. Lockfiles are the superior mechanism.

## Decision

Replace current package configuration mechanisms with one that is purely lockfile centric. The GUI should be simpler to work with than a vanilla lockfile.

## Consequences

The cruiz UI and recipe management will change significantly, as will the settings stored per recipe. The focus must change to be centric around the dependency graph and managing that.

For instance, profiles and options will no longer be the focus against the recipe. Instead, it's how the recipe interacts with the dependency graph.

Simple lockfiles must be creatable. This is essentially what profile and options are.

Referencing external lockfiles should also be possible. A use case for this is to use a lockfile from a downstream application that uses a package created from the current recipe.

Lockfile management should include
* setting options for _any_ package in the dependency graph
* changing versions of any package in the dependency graph

Any package in the dependency graph should also be rebuildable.
