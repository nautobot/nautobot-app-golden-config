# E3XXX Details

## Message emitted:

`E3XXX: Un-Registered Error Code used.`

## Description:

This means a code snippet was calling get_error_code() with an error code that is not registered.

## Troubleshooting:

Find the error code in the traceback, and search for it in the codebase.

## Recommendation:

Add the error code to the `error_codes.py` file.