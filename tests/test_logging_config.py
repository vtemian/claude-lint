import logging

from claude_lint.logging_config import get_logger, setup_logging


def test_setup_logging_default():
    """Test default logging setup."""
    setup_logging()
    logger = get_logger(__name__)
    assert logger.getEffectiveLevel() == logging.WARNING


def test_setup_logging_verbose():
    """Test verbose logging setup."""
    setup_logging(verbose=True)
    logger = get_logger(__name__)
    assert logger.getEffectiveLevel() == logging.INFO


def test_setup_logging_quiet():
    """Test quiet logging setup."""
    setup_logging(quiet=True)
    logger = get_logger(__name__)
    assert logger.getEffectiveLevel() == logging.ERROR


def test_get_logger():
    """Test getting named logger."""
    logger = get_logger("test.module")
    assert logger.name == "claude_lint.test.module"
