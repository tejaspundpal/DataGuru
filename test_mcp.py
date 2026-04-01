import asyncio
import sys
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp():
    server_script = Path(__file__).parent / "src" / "mcp_github_server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        env=os.environ.copy()
    )
    print("Starting client...", server_script)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Calling tool...")
            try:
                result = await session.call_tool("fetch_repo_contents", arguments={})
                print(f"Error flag: {result.isError}")
                for content in result.content:
                    print(f"Content Type: {content.type}")
                    if content.type == "text":
                        print(f"Content text length: {len(content.text)}")
                        print(f"Content text preview: {content.text[:100]}")
            except Exception as e:
                print(f"Tool call failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp())
