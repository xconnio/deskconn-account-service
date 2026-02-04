.PHONY: setup
-include .env
export $(shell sed 's/=.*//' .env 2>/dev/null || true)

REQUIRED_VARS = DESKCONN_ACCOUNT_AUTHID DESKCONN_ACCOUNT_PRIVATE_KEY

# check for missing or empty envs
define check_defined
    @: $(foreach v,$(1),$(if $(filter-out "",$(strip $($(v)))),,$(error Missing or empty environment variable: $(v))))
endef

install_uv:
	@if ! command -v uv >/dev/null 2>&1; then \
  		curl -LsSf https://astral.sh/uv/install.sh | sh; \
  	fi

setup:
	cp example.env .env
	make install_uv
	uv venv
	uv pip install -e .[test] -U

format:
	./.venv/bin/ruff format .

lint:
	./.venv/bin/ruff check .

test:
	./.venv/bin/pytest -s -v tests

clean:
	rm -rf *.egg-info build

run:
	$(call check_defined,$(REQUIRED_VARS))
	./.venv/bin/xcorn main:app \
		--realm io.xconn.deskconn \
		--url ws://localhost:8080/ws \
		--authid $(DESKCONN_ACCOUNT_AUTHID) \
		--private-key $(DESKCONN_ACCOUNT_PRIVATE_KEY)

migration:
	./.venv/bin/alembic revision --autogenerate -m "$(name)"

migrate:
	./.venv/bin/alembic upgrade head

build-docker:
	docker build -t xconnio/deskconn-account:latest .

run-docker:
	docker compose up
