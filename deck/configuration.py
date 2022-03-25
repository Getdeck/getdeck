import sys
import logging

console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)

logger = logging.getLogger("deck")
logger.addHandler(console)

__VERSION__ = "0.1.0"