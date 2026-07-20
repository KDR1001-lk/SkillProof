"""Skill-verification hiring platform — ADK agent.

Repurposed from the CodeQuest Academy scaffold.  Two tools let the LLM
fetch code from a public GitHub repo and generate quiz questions that
verify whether a candidate actually authored (or deeply understands)
that code.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error

import dotenv
from google.adk.agents import Agent

dotenv.load_dotenv()

# ---------------------------------------------------------------------------
# File extensions we consider "real source code" (skip configs / locks / etc.)
# ---------------------------------------------------------------------------
_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".cpp", ".c", ".h", ".cs", ".kt", ".swift", ".scala", ".lua",
    ".php", ".ex", ".exs", ".hs", ".ml", ".r", ".jl",
}

_SKIP_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", ".gitignore", ".editorconfig",
    "LICENSE", "LICENSE.md", "CHANGELOG.md",
}


def _github_api_get(url: str) -> dict | list | None:
    """Simple GET against the GitHub REST API (unauthenticated)."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkillVerifyAgent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def _parse_owner_repo(repo_url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from various GitHub URL formats."""
    # https://github.com/owner/repo  or  github.com/owner/repo
    m = re.match(
        r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        repo_url.strip(),
    )
    if m:
        return m.group(1), m.group(2)
    return None


# ---------------------------------------------------------------------------
# TOOL 1 — fetch_github_repo
# ---------------------------------------------------------------------------
def fetch_github_repo(repo_url: str) -> dict:
    """Fetch the README and the largest non-trivial source file from a
    public GitHub repository.

    Args:
        repo_url: Full URL of a public GitHub repo,
                  e.g. https://github.com/owner/repo

    Returns:
        A dict with 'readme' text, chosen 'filename', and 'code' text,
        or an error message.
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return {"status": "error", "message": f"Cannot parse GitHub URL: {repo_url}"}

    owner, repo = parsed
    api_base = f"https://api.github.com/repos/{owner}/{repo}"

    # --- README -----------------------------------------------------------
    readme_data = _github_api_get(f"{api_base}/readme")
    readme_text = ""
    if readme_data and "content" in readme_data:
        import base64
        try:
            readme_text = base64.b64decode(readme_data["content"]).decode(
                errors="replace"
            )
        except Exception:
            readme_text = "(could not decode README)"
    elif readme_data and "message" in readme_data:
        readme_text = "(no README found)"

    # --- Source tree (default branch, recursive) --------------------------
    tree_data = _github_api_get(f"{api_base}/git/trees/HEAD?recursive=1")
    if not tree_data or "tree" not in tree_data:
        return {
            "status": "error",
            "message": (
                "Could not fetch the file tree.  The repo may be empty, "
                "private, or the GitHub API rate limit was hit."
            ),
        }

    # Pick the largest source file that isn't a config / lock / etc.
    best_file = None
    best_size = 0
    for item in tree_data["tree"]:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        name = path.rsplit("/", 1)[-1]
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        size = item.get("size", 0)
        if ext.lower() not in _SOURCE_EXTENSIONS:
            continue
        if name in _SKIP_NAMES:
            continue
        if size > best_size:
            best_size = size
            best_file = path

    if not best_file:
        return {
            "status": "error",
            "message": "No recognisable source files found in the repo.",
        }

    # Fetch the raw content of the chosen file
    raw_url = (
        f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{best_file}"
    )
    req = urllib.request.Request(raw_url, headers={"User-Agent": "SkillVerifyAgent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code_text = resp.read().decode(errors="replace")
    except Exception:
        return {
            "status": "error",
            "message": f"Could not download {best_file}.",
        }

    # Truncate very large files so the LLM context isn't blown
    max_chars = 12_000
    if len(code_text) > max_chars:
        code_text = code_text[:max_chars] + "\n\n... [truncated] ..."

    return {
        "status": "success",
        "repo": f"{owner}/{repo}",
        "readme_snippet": readme_text[:2000],
        "filename": best_file,
        "code": code_text,
    }


# ---------------------------------------------------------------------------
# TOOL 2 — generate_quiz
# ---------------------------------------------------------------------------
def generate_quiz(code_snippet: str) -> dict:
    """Prepare a quiz payload for the LLM to use when questioning a candidate.

    This tool does NOT call the LLM itself — it packages the code snippet
    and a quiz-generation prompt so that the *agent* (which IS the LLM)
    can produce the questions in its next response.

    Args:
        code_snippet: The source code to base quiz questions on.

    Returns:
        A dict containing the code and the quiz-generation prompt for
        the agent to follow.
    """
    if not code_snippet or not code_snippet.strip():
        return {"status": "error", "message": "Empty code snippet provided."}

    prompt = (
        "Based on the following code, generate exactly 3 short quiz questions "
        "that the real author of this code should be able to answer easily.  "
        "Mix of question types: include at least one multiple-choice question "
        "(with 4 options labelled A-D) and at least one short-answer question.  "
        "For each question also provide the correct answer.  "
        "Format your output EXACTLY as follows:\n\n"
        "Q1: <question text>\n"
        "   A) ... B) ... C) ... D) ...   (if multiple choice)\n"
        "   ANSWER: <correct answer>\n\n"
        "Q2: <question text>\n"
        "   ANSWER: <correct answer>\n\n"
        "Q3: <question text>\n"
        "   A) ... B) ... C) ... D) ...   (if multiple choice)\n"
        "   ANSWER: <correct answer>\n\n"
        "--- CODE START ---\n"
        f"{code_snippet}\n"
        "--- CODE END ---"
    )

    return {
        "status": "success",
        "quiz_generation_prompt": prompt,
    }


# ---------------------------------------------------------------------------
# ROOT AGENT
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="codequest_agent",          # keep original package name for adk discovery
    model="gemini-3.1-flash-lite",
    description=(
        "A skill-verification hiring agent that quizzes candidates on "
        "their own GitHub code to confirm authorship and understanding."
    ),
    instruction="""\
You are **SkillVerify**, a friendly but rigorous technical interviewer for a
skill-verification hiring platform.

### Your workflow

1. **Greet** the user and ask for a public GitHub repository URL.
2. Call **fetch_github_repo** with that URL.
   - If it errors, tell the user and ask for another URL.
   - On success, briefly describe the repo (from the README) and the source
     file you selected.
3. Call **generate_quiz** with the code returned by fetch_github_repo.
4. Read the quiz_generation_prompt from the tool result. Follow those
   instructions to produce exactly 3 quiz questions (mix of multiple-choice
   and short-answer) that the real author should be able to answer.
5. **Present only the questions to the user — do NOT reveal the answers.**
   Number them Q1, Q2, Q3.
6. Wait for the user to answer.
7. Once the user provides answers, compare them to your correct answers.
   Be generous with phrasing — accept semantically equivalent answers.
   Give a final score out of 3 and brief feedback on each question.

### Rules
- Never reveal correct answers before the user attempts them.
- If the user asks to skip or gives up, reveal the answers and score 0.
- Keep quiz questions focused on logic, design decisions, and
  implementation details — not trivia like line numbers or variable names.
- Stay encouraging and professional.  This is a demo, keep it light.
""",
    tools=[
        fetch_github_repo,
        generate_quiz,
    ],
)
