#!/bin/bash
KMP_DUPLICATE_LIB_OK=TRUE .venv/bin/python -m uvicorn backend.main:app --reload --port 8000
