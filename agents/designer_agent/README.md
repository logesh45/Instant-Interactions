# Designer Agent for Micro-Interaction Generator

This agent is designed to generate, verify, and auto-correct UI micro-interaction code snippets (HTML, CSS, and minimal JS) for frontend development. It leverages the Google ADK Agent framework and integrates with Playwright for headless verification.

## Features
- **Generates** high-quality, self-contained UI micro-interaction code snippets.
- **Verifies** generated code using Playwright in a headless environment.
- **Auto-corrects** code if verification fails, attempting one fix before reporting errors.
- **Supports** Bootstrap and Tailwind CSS via CDN, and uses [picsum.photos](https://picsum.photos) for placeholder images.

## How It Works
1. **Understands User Request:**
   - Infers the required micro-interaction and target element (e.g., button, input, div).
2. **Generates Code:**
   - Produces minimal HTML with generic class names, comprehensive CSS, and minimal JS (if needed).
   - If using Bootstrap or Tailwind, automatically includes the appropriate CDN links in the generated HTML.
   - Uses `https://picsum.photos` for any required placeholder images.
3. **Prepares for Verification:**
   - Wraps the snippet into a complete HTML document.
   - Ensures the correct CSS framework CDN is included.
4. **Verifies with Playwright:**
   - Uses Playwright MCP tools to render the HTML and capture errors, logs, and screenshots.
5. **Auto-corrects if Needed:**
   - If verification fails, attempts to fix the code and re-verify once.
6. **Responds with Results:**
   - Returns the code, verification status, errors (if any), and screenshot info.


## License
This project is intended for internal or research use. Please see your organization’s licensing policies.

---

