import os
import json
# from dotenv import load_dotenv # REMOVED - Assuming ADK handles .env loading

_AGENT_FILE_BASENAME = os.path.basename(__file__)
print(f"[Agent {_AGENT_FILE_BASENAME}] Script started. Expecting environment variables to be pre-loaded by ADK or shell.")

# Import ADK Agent class and MCPToolSet components
try:
    from google.adk.agents import Agent
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
except ImportError as e:
    print(f"!!! ERROR (Agent {_AGENT_FILE_BASENAME}): Failed to import ADK or MCPToolSet components: {e}. !!!")
    print(f"!!! Ensure 'google-adk' and 'google-mcp-tools' are installed. !!!")
    raise

print(f"[Agent {_AGENT_FILE_BASENAME}] ADK and MCPToolSet components imported.")

# --- Configuration (now directly from os.getenv, assuming ADK or shell loaded them) ---
# The AGENT_MODEL_NAME used by the Agent constructor.
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gemini-2.0-flash") # Default if not in env

# Command and arguments for launching the stdio-based Playwright MCP server.
# These MUST be correctly set in your environment (e.g., via .env file loaded by ADK).
PLAYWRIGHT_MCP_COMMAND = os.getenv("PLAYWRIGHT_MCP_COMMAND")
PLAYWRIGHT_MCP_ARGS_STR = os.getenv("PLAYWRIGHT_MCP_ARGS", '[]') # Default to empty JSON list string

print(f"[Agent {_AGENT_FILE_BASENAME}] Agent Model (from env or default): {AGENT_MODEL_NAME}")
print(f"[Agent {_AGENT_FILE_BASENAME}] Playwright MCP Command (from env): {PLAYWRIGHT_MCP_COMMAND}")
print(f"[Agent {_AGENT_FILE_BASENAME}] Playwright MCP Args String (from env or default): {PLAYWRIGHT_MCP_ARGS_STR}")

playwright_mcp_args_list = []
if PLAYWRIGHT_MCP_ARGS_STR:
    try:
        playwright_mcp_args_list = json.loads(PLAYWRIGHT_MCP_ARGS_STR)
        if not isinstance(playwright_mcp_args_list, list):
            print(f"[Agent {_AGENT_FILE_BASENAME}] !!! WARNING: PLAYWRIGHT_MCP_ARGS from env is not a valid JSON list. Parsed: {playwright_mcp_args_list} !!!")
            playwright_mcp_args_list = [] # Reset if not a list
    except json.JSONDecodeError as e:
        print(f"[Agent {_AGENT_FILE_BASENAME}] !!! WARNING: Could not parse PLAYWRIGHT_MCP_ARGS JSON string '{PLAYWRIGHT_MCP_ARGS_STR}'. Error: {e} !!!")
        playwright_mcp_args_list = []
else:
    print(f"[Agent {_AGENT_FILE_BASENAME}] PLAYWRIGHT_MCP_ARGS_STR is empty or not set.")

playwright_mcp_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=["-y", "@executeautomation/playwright-mcp-server"]
            )
        )
# --- Define and Instantiate the Agent ---
try:
    print(f"[Agent {_AGENT_FILE_BASENAME}] Attempting to create root_agent instance.")
    root_agent = Agent(
        name="micro_interaction_generator_agent",
        model=AGENT_MODEL_NAME,
        description=(
            "Generates and suggests UI micro-interaction code, verifies it headlessly (capturing errors/screenshots), and can attempt fixes."
        ),
        instruction=(
            "You are an expert Interaction Designer and Frontend Developer. Your primary goal is to generate high-quality, self-contained UI micro-interaction code snippets (HTML, CSS, and minimal JS if essential) and then verify them using Playwright tools.\n\n"
            "**Workflow:**\n"
            "1.  **Understand User Request:** User will describe a UI micro-interaction. Extract the core `description` and infer a `target_element_hint` (e.g., 'button', 'input', 'div').\n\n"
            "2.  **Generate Code Snippet (Your LLM Task):** Based on the user's description, YOU will directly generate the HTML and CSS code. Adhere to these guidelines:\n"
            "    a.  Minimal HTML, generic class names (e.g., `interactive-element`).\n"
            "    b.  Comprehensive CSS in `<style>` tags for smooth, standard animations.\n"
            "    c.  Minimal vanilla JS in `<script>` tags, only if CSS-only is impossible.\n"
            "    d.  The entire snippet (HTML, style, script) must be a single self-contained string.\n"
            "    e.  **Frameworks & CDNs:** If using Bootstrap/Tailwind classes, YOU MUST include their CDN links (Bootstrap CSS CDN or Tailwind Play CDN script tag) in the `<head>` of the full HTML document you prepare for verification (see step 3a).\n"
            "    f.  **If your code or the user's prompt requires an image or placeholder image, ALWAYS use a URL from https://picsum.photos (e.g., https://picsum.photos/300/200) as the image source.**\n\n"
            "**MANDATORY VERIFICATION:**\n"
            "You must always perform at least one verification of your generated code using the Playwright tool, even if the code appears correct. Do not skip this step under any circumstances.\n\n"
            "3.  **Prepare for Verification:**\n"
            "    **ALWAYS wrap any user-provided HTML/CSS/JS snippet into a complete, valid HTML document before verification. If the user provides only a snippet, you must generate the necessary <html>, <head>, and <body> tags.**\n"
            "    **BEFORE verifying with Playwright, infer which CSS library (if any) is being used (e.g., Tailwind, Bootstrap) and ensure the correct CDN link is included in the <head> of the HTML document.**\n"
            "    a.  Construct a **full HTML document string** for Playwright. Structure:\n"
            "        `<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><title>Verification</title><style>body {{ margin: 20px; }}</style>[CSS_LIBRARY_CDN]</head><body>[YOUR_GENERATED_SNIPPET]</body></html>`\n"
            "        - Replace [CSS_LIBRARY_CDN] with the appropriate <link> or <script> tag for the inferred CSS framework, if used.\n"
            "    b. Identify the Playwright tool to use. You have tools from `playwright_stdio_service`. **Inspect the actual loaded tool names and their arguments when the agent starts.** For example, you might have a tool like `playwright_stdio_service.render_html_and_capture_details` that accepts `html_content: str`.\n\n"
            "4.  **Verify Code with Playwright Tool:** Call the identified `playwright_stdio_service` tool with the full HTML document string.\n\n"
            "5.  **Analyze Verification Result:** The Playwright tool will return results (e.g., console logs, errors, maybe a screenshot path or base64 image).\n"
            "    a.  If no console errors (or only expected logs) and success: Respond to the user with the original code snippet, state successful verification, and include any screenshot information if available from the tool.\n"
            "    b.  If console errors are reported: **Self-correction step.** Re-evaluate your original code snippet alongside the error messages. Try to fix the code. After fixing, go back to step 3 to prepare and re-verify the *newly fixed* code. If successful, provide fixed code. If it still fails after one fix attempt, provide the last attempted code and list the remaining errors and any screenshot data.\n\n"
            "6.  **Final Response:** Primarily the code snippet, with clear verification status, errors (even after fixes), and screenshot info. Be concise. If a tool call itself fails operationally, report that."
        ),
        tools=[playwright_mcp_toolset]
    )
    print(f"[Agent {_AGENT_FILE_BASENAME}] 'root_agent' created successfully.")

except Exception as e:
    print(f"[Agent {_AGENT_FILE_BASENAME}] !!! CRITICAL ERROR instantiating 'root_agent': {e} !!!")
    root_agent = None # Define as None so the module doesn't break on import if adk-web tries to load it

if root_agent is None:
    print(f"[Agent {_AGENT_FILE_BASENAME}] 'root_agent' is None due to an earlier instantiation error. ADK Web may not function correctly.")