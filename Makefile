.PHONY: setup
setup:
	python3 setup/build_database.py
	python3 setup/clean_questions.py