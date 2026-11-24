pytest -m "not slow" # 6 fast tests, under a second
pytest # all 22 tests, about 2 minutes
python run_engine.py --quick # smoke test: the model still solves at cruise (about 2 minutes)
