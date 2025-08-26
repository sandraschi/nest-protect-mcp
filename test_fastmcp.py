import asyncio
from fastmcp import FastMCP
from fastmcp.messages import Message

async def main():
    # Create a simple FastMCP instance
    mcp = FastMCP("test-app")
    
    # Print available methods and attributes
    print("FastMCP instance created successfully!")
    print(f"Available methods: {[m for m in dir(mcp) if not m.startswith('_')]}")
    
    # Try to create a message
    try:
        msg = Message(method="test", params={"key": "value"})
        print(f"Message created: {msg}")
    except Exception as e:
        print(f"Error creating message: {e}")

if __name__ == "__main__":
    asyncio.run(main())
