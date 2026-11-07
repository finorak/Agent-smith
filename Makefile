SANDOX := sandbox
PYTHON_IMAGE := python:3.13-slim

SERVER_TYPE ?= "http"

UV := uv

docker-pull:
	docker pull $(PYTHON_IMAGE)

install: docker-pull
	$(UV) sync

run-sandbox:
	@if [ "$(SERVER_TYPE)" = "http" ]; then \
		$(UV) run python -m $(SANDOX) --mcp-server 'http://localhost:8000/mcp'; \
	else \
		$(UV) run python -m $(SANDOX) --mcp-stdio 'python $(SERVER_TYPE)'; \
	fi

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

fclean: clean
	rm -rf .venv

re: fclean install

.PHONY := install run-sandbox debug clean fclean docker-pull
