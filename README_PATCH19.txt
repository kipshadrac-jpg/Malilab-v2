Patch 19: Plan Notepad backend. New app "notepad": private notes made of typed blocks, version history,
markdown export, the notes API, and a tested calculation engine with its API. Needs patches 17 and 18.
Adds two tables, so run migrate. The engine tests need no database:  python -m unittest notepad.test_engine
