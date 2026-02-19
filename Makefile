jobload:
	cd src/jobload && python3 build.py

build: jobload

clean:
	cd src/jobload && rm -vrf build *.so *.c __pycache__

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  jobload - Build the jobload package"
	@echo "  build   - Alias for 'jobload'"
	@echo "  clean   - Remove build artifacts"
	@echo "  help    - Show this help message"

.PHONY: jobload build clean
