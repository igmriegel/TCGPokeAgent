# Deck-bound RFL profiles

Each directory binds a deck identity and SHA-256 to a promoted policy profile.
The runtime uses a profile only when both identity and hash validate; otherwise it
falls back to the frozen heuristic baseline.
