# Design

This file is intended to start collecting/discussing architectural & feature design questions.
Future refactoring, tests and features will be based on this document.

## Command: deck get

```mermaid
flowchart TD
    command-called["start"] --> deck-fetch["fetch deck"]
    deck-fetch --> deck-render[render deck]
    deck-render --> sources-fetch["fetch & validate sources"]
    sources-fetch --> cluster-setup["setup cluster"]
    cluster-setup --> sources-apply["apply sources"]

```

Current Problems:

- temporary folders and files are not persisted long enough

Feature Ideas:

- cache
- override
- templating
  - env
  - secrets
