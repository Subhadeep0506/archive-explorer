"""
Startup script for running uvicorn with Windows-compatible event loop.
This ensures psycopg async operations work correctly on Windows.
"""
import asyncio
import sys
import os

if __name__ == "__main__":
    # Fix for Windows: Create a SelectorEventLoop explicitly before uvicorn starts
    if sys.platform == 'win32':
        import selectors
        selector = selectors.SelectSelector()
        loop = asyncio.SelectorEventLoop(selector)
        asyncio.set_event_loop(loop)
        print("[INFO] Windows detected: Using SelectorEventLoop for psycopg compatibility")
    
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    
    # Run uvicorn with the manually created event loop
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    if sys.platform == 'win32':
        # Run with the existing loop we created
        loop.run_until_complete(server.serve())
        loop.close()
    else:
        server.run()
