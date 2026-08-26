"""PRAHARI adapters — ALL I/O lives here (network, files, clock, env, database).

🔴 The engine is pure and does none of this. Adapters fetch/read the world, convert it
to plain data, and hand it to engine functions. Every external system sits behind an
interface with >=2 implementations so a provider swap is a config change (PRD §29.7).
"""
