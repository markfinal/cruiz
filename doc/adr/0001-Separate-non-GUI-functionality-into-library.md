# 1. Separate non GUI functionality into library

Date: 2025-01-02

## Status

Proposed

## Context

GUI code is hard to write tests for. There is a desire to have more tests to harden the code.

## Decision

Separate non-GUI code, into a separate library package, in the same repository. Library code will depend on QtCore at most.

## Consequences

Tests will be written for, and run against, the library package.

GUI code will use the library code, making the GUI code more straightforward.

A dependency on QtCore allows Qt style containers, models, etc to be used in the library code to avoid needing an interop layer between it and GUI code.
