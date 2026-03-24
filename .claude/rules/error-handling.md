# Error Handling

## Exception hierarchy
All exceptions must inherit from `AcliError`. Never raise stdlib exceptions directly.

```
AcliError
├── AcliNotFoundError    # acli binary not installed
├── AcliAuthError        # authentication failure
├── AcliTimeoutError     # command timeout
└── AcliValidationError  # input validation failure
```

## Logging levels
- ERROR: command failure, unrecoverable errors
- WARNING: auth retry, fallback behavior
- DEBUG: acli command args, raw stdout/stderr

## Retry policy
- Auth expiry (401): retry once after re-authentication
- All other errors: no retry, raise immediately
- Include acli stderr message in exception verbatim
