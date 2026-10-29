SRC := src

UV := uv

install:
	$(UV) sync

run:
	$(UV) run python -m $(SRC)

debug:
	$(UV) run pdb -m $(SRC).__main__.py

.PHONY := install run debug
