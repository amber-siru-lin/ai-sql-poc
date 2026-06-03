.PHONY: onboard setup dev check test ui-build

onboard:
	./scripts/onboard.sh

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

check:
	./scripts/onboard.sh --check

test:
	scripts/py -m pytest tests/ -q

ui-build:
	cd ui && npm run build
