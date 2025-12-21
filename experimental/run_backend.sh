#!/bin/bash
KMP_DUPLICATE_LIB_OK=TRUE /Users/abhi/opt/anaconda3/bin/python3 -m uvicorn backend.main:app --reload --port 8000
