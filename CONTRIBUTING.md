# Contributing to Nest Protect MCP

Thank you for your interest in contributing to Nest Protect MCP! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up a development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them with a descriptive message
3. Push your changes to your fork
4. Open a pull request against the `main` branch

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for all function parameters and return values
- Include docstrings for all public functions and classes
- Keep lines under 100 characters
- Run `black`, `isort`, and `flake8` before committing

## Testing

- Write tests for new features and bug fixes
- Run tests locally with `pytest`
- Ensure all tests pass before submitting a pull request
- Update documentation as needed

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Ensure your code passes all tests and linting checks
3. Open a pull request with a clear title and description
4. Reference any related issues in your PR description

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
