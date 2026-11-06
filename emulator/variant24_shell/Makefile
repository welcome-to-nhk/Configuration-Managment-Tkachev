PYTHON ?= python3

.PHONY: run test demo

run:
	$(PYTHON) src/shell_emulator.py --vfs vfs

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	$(PYTHON) src/shell_emulator.py --vfs vfs --script scripts/demo_stage3.txt
