SANDOX := sandbox

UV := uv

install:
	$(UV) sync

run-sandbox:
	$(UV) run python $(SANDOX)

debug:
	$(UV) run pdb -m $(SANDOX).__main__.py

lint:
	$(UV) run flake8 --exclude=.venv
	$(UV) run mypy .

lint-strict: lint
	$(UV) run mypy --strict .

.PHONY := install run-sandbox debug
