"""PRAHARI engine — 🔴 PURE. The science.

Nothing in this package may perform I/O, read the clock, use randomness, or read
the environment. This is enforced by tests/test_purity.py (PRD §25.3). Adapters do
all I/O and pass plain data into these functions; that is what keeps the science
deterministic and unit-testable offline.
"""
