# Contributing to Helix Platform

Thank you for your interest in contributing to Helix Platform! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your changes (`git checkout -b feature/amazing-feature`)
4. **Make your changes** following our code standards
5. **Write tests** for your changes
6. **Commit your changes** with clear messages
7. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Clone repository
git clone https://github.com/Deathcharge/helix-platform.git
cd helix-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

## Code Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to all functions and classes

### Example

```python
def process_agent_response(
    agent_name: str,
    response: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Process a response from an agent.
    
    Args:
        agent_name: Name of the agent
        response: Response text from agent
        timeout: Processing timeout in seconds
        
    Returns:
        Dictionary containing processed response
        
    Raises:
        TimeoutError: If processing exceeds timeout
    """
    # Implementation
    pass
```

## Testing

### Write Tests

All new features must include tests:

```python
def test_agent_registration():
    """Test that agents can be registered"""
    orchestrator = HelixOrchestrator()
    orchestrator.register_agent("test", "Gemini")
    assert "test" in orchestrator.agents
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_orchestration.py::test_agent_registration -v

# Run with coverage
pytest tests/ --cov=helix_platform --cov-report=html
```

### Coverage Requirements

- Minimum 80% code coverage
- All public methods must have tests
- Integration tests required for new features

## Documentation

### Update Documentation

- Update relevant `.md` files in `docs/`
- Add docstrings to code
- Include examples for new features
- Update API reference if needed

### Documentation Standards

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation up-to-date with code

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add consensus voting mechanism

- Implement supermajority voting strategy
- Add unanimous consensus option
- Add tests for voting logic
- Update documentation

Fixes #123
```

### Commit Message Format

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Test additions/changes
- **chore**: Build/dependency changes

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass** (`pytest tests/ -v`)
4. **Check code coverage** (minimum 80%)
5. **Request review** from maintainers
6. **Address feedback** and update PR
7. **Merge** once approved

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update

## Testing
- [ ] Added tests
- [ ] All tests pass
- [ ] Coverage maintained

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
```

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- Minimal code example

### Feature Requests

Include:
- Use case and motivation
- Proposed solution
- Alternative approaches
- Example usage

## Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Discord**: Join our community server
- **Twitter**: Follow @HelixCollective

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Apache 2.0 / Proprietary).

---

Thank you for contributing to Helix Platform! 🙏
