import logging
from rich.logging import RichHandler


def setup_logger():
    """Настраивает базовую конфигурацию логирования."""
    logging.basicConfig(
        level="INFO",
        format="[blue]%(levelname)s:     %(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_level=False,
                show_time=False,
                show_path=False,
            ),
        ],
    )


# Инициализируем настройки при импорте модуля
setup_logger()
