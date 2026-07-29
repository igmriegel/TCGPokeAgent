# Vendored CABT helper

This directory is copied from the official `cg-lib` submission asset used by
the competition sample notebook. It provides the canonical card/attack catalog,
observation dataclasses, search bindings, and Linux CABT native library expected
inside a Kaggle submission package.

Source artifact inspected on 2026-07-29:
`kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck`.

The files are vendored without source edits. Their use and redistribution
remain subject to the Kaggle competition rules. Project Ruff and mypy checks
exclude this directory; package validation still checks Python 3.11 syntax and
loads the extracted agent through the real CABT file-agent path.
