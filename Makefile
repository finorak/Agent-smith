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


clean:
	find . -name "*.pyc" -exec rm -rf {} +
	find . -type d \( -name "__pycache__" -o -name ".mypy_cache" \) -exec rm -rf {} +

fclean:
	rm -rf .venv

re: fclean install

.PHONY := install run-sandbox debug clean fclean
