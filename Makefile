# USB Camera Test Suite - Makefile
# Cross-platform build automation

.PHONY: help install install-dev test lint format clean build build-exe package all

# Default target
help:
	@echo "USB Camera Test Suite - Build Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install package in development mode"
	@echo "  install-dev  Install with development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test         Run test suite"
	@echo "  lint         Run code linting"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "Building:"
	@echo "  build        Build Python packages (wheel + sdist)"
	@echo "  build-exe    Build standalone executable"
	@echo "  package      Create installer packages"
	@echo "  all          Build everything"
	@echo ""
	@echo "Platform-specific:"
	@echo "  install-unix Install on Unix-like systems"
	@echo "  install-win  Install on Windows"
	@echo ""

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

install-unix:
	@echo "Running Unix installer..."
	chmod +x install.sh
	./install.sh

install-win:
	@echo "Running Windows installer..."
	install.bat

# Development targets
test:
	python -m pytest tests/ -v --cov=camera_test_suite --cov-report=html --cov-report=term

lint:
	flake8 camera_test_suite/ tests/
	mypy camera_test_suite/

format:
	black camera_test_suite/ tests/
	isort camera_test_suite/ tests/

# Cleaning
clean:
	python build.py --clean-only
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Building targets
build:
	python setup.py sdist bdist_wheel

build-exe:
	python build.py

package:
	python build.py

all: clean build build-exe package

# Quick test run
quick-test:
	python -m camera_test_suite.cli --list-cameras

# Development server (GUI)
dev:
	python -m camera_test_suite

# Show project info
info:
	@echo "Project: USB Camera Test Suite"
	@echo "Version: 1.0.0"
	@echo "Python: $(shell python --version)"
	@echo "Platform: $(shell python -c 'import platform; print(platform.system())')"
	@echo "Directory: $(shell pwd)"

# Dependency check
check-deps:
	@echo "Checking dependencies..."
	@python -c "import cv2; print('✓ OpenCV:', cv2.__version__)"
	@python -c "import PIL; print('✓ Pillow:', PIL.__version__)"
	@python -c "import numpy; print('✓ NumPy:', numpy.__version__)"
	@python -c "import matplotlib; print('✓ Matplotlib:', matplotlib.__version__)"
	@python -c "import reportlab; print('✓ ReportLab:', reportlab.Version)"
	@python -c "import psutil; print('✓ psutil:', psutil.__version__)"

# Release preparation
prepare-release:
	@echo "Preparing release..."
	$(MAKE) clean
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) all
	@echo "Release preparation complete!"

# Docker targets (if needed in future)
docker-build:
	@echo "Docker build not implemented yet"

docker-run:
	@echo "Docker run not implemented yet"