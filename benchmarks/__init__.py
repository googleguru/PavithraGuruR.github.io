from .shared import Circuit
from .iscas85 import CIRCUITS_85
from .iscas89 import CIRCUITS_89

# Combined registry: ISCAS '85 first, then '89
CIRCUITS: dict[str, callable] = {**CIRCUITS_85, **CIRCUITS_89}
