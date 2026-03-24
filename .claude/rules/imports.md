# Import Order

Always follow this order, separated by blank lines:

```python
# 1. __future__
from __future__ import annotations

# 2. stdlib
import asyncio
import json

# 3. third-party
from pydantic import BaseModel, Field

# 4. local
from pyacli.lib.exceptions import AcliError
```

isort compatible. No wildcard imports (`from x import *`).
