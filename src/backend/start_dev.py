#!/usr/bin/env python3
"""
Optimized development server startup script with proper reload exclusions
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "_test/*",
            "_test/**/*",
            "__pycache__/*",
            "*.pyc",
            "*.log",
            "*.db",
            "*.json.backup",
            ".pytest_cache/*",
            "assets/*",
            "models/*",
        ],
        log_level="info"
    )
