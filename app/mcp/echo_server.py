"""
Minimal MCP server stub.

Replace the `echo` tool with theme-specific tools (e.g., `pptx.scan_slide`,
`pptx.apply_bulk_fix`) once the problem is frozen. Keep Easy Auth wiring
in front of this server when hosted on Azure App Service / Container Apps.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("msft-hackathon-mcp")


@mcp.tool()
def echo(text: str) -> str:
    """Echo the input string. Used to validate MCP transport end-to-end."""
    return text


if __name__ == "__main__":
    mcp.run()
