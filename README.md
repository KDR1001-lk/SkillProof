# CodeQuest Academy

CodeQuest Academy is a beginner-friendly, story-driven [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) demo for university workshops. Aang guides students through programming missions and uses Python function tools to recommend missions, describe them, and check whether a student is ready to begin. The fan-made theme draws on the Earth Kingdom journey, Toph, and Ba Sing Se from Netflix's *Avatar: The Last Airbender* Season 2.

> This unofficial educational demo is not affiliated with or endorsed by Netflix, Nickelodeon, or the creators of *Avatar: The Last Airbender*.

## Features

- A single ADK agent with a clear `root_agent` entry point
- Six Earth Kingdom missions based on common programming challenges
- Tools for listing quests, retrieving details, and checking hero readiness
- On-demand mission illustrations saved as ADK session artifacts
- A warm, playful Aang-inspired guide designed to make agent concepts approachable

## Quest catalogue

| Difficulty | Quest | Boss | Skill focus |
| --- | --- | --- | --- |
| Novice | The Unsteady Cabbage Cart | The Fencepost Badgermole | Loop boundaries |
| Novice | The Null-Vine Marsh | The Vanishing Vine | Null checks |
| Apprentice | The Echoing Crystal Catacombs | The Endless Echo | Base cases |
| Apprentice | The Big-O Boulder Run | The Quadratic Quarry | Algorithm analysis |
| Master | The Great Wall Merge Crisis | The Conflicting Gatekeeper | Git branching |
| Master | The Twin-Gate Deadlock | The Waiting Gatekeepers | Concurrency |

## Project structure

```text
.
├── codequest_agent/
│   ├── __init__.py
│   └── agent.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Local credentials, virtual environments, Python caches, and ADK session data are excluded from Git.

## Prerequisites

- Python 3.10 or newer
- A Google AI Studio API key or a configured Google Cloud project

## Setup

1. Clone the repository and enter its directory.

   ```bash
   git clone <your-repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment.

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install the dependencies.

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file.

   macOS/Linux:

   ```bash
   cp .env.example .env
   ```

   Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Edit `.env` and provide either your Google AI Studio API key or your Vertex AI project settings. Never commit this file.

Image generation uses `gemini-3.1-flash-image` by default. You can override it by
setting `CODEQUEST_IMAGE_MODEL` in `.env`. Your Google project or API key must have
access to the selected image model.

## Run the agent

From the repository root, with the virtual environment active, run:

```bash
adk web
```

Open the local URL printed by ADK and select `codequest_agent`.

## Example prompts

Start a journey:

- “Hi Aang! My name is Maya and I am level 1. Help me choose my first mission.”
- “I am new to coding. What novice missions can I try?”
- “Help me restore balance to my programming skills.”

Explore missions:

- “Show me the novice quests.”
- “Tell me about QUEST-RECURSION.”
- “What skills and XP can I earn from the Big-O Boulder Run?”
- “Show me every mission available on the road to Ba Sing Se.”

Check readiness:

- “I am level 4. Am I ready for the Big-O Boulder Run?”
- “Aang, I am level 10. Can I attempt QUEST-MERGECONFLICT?”
- “I want to face the Twin-Gate Deadlock. My current level is 8.”

Ask for guidance:

- “I know loops but struggle with recursion. Which mission should I investigate?”
- “Recommend a mission for a level 6 student and explain why it fits.”
- “I entered an unknown quest ID. Can you show me the valid choices?”

Create images:

- “Create a 16:9 image of Aang arriving at the gates of Ba Sing Se with Appa.”
- “Illustrate the Big-O Boulder Run as an exciting coding-training scene.”
- “Make a square mission badge for QUEST-RECURSION with glowing crystal tunnels.”
- “Generate a vertical poster of Aang restoring balance to a city made of code.”

## How it works

[`codequest_agent/agent.py`](codequest_agent/agent.py) defines the quest data, four function tools, and the ADK agent:

- `list_quests` lists all quests or filters them by difficulty.
- `get_quest_details` returns the complete data for one quest.
- `check_quest_readiness` compares a hero's level with the quest requirement.
- `create_mission_image` generates a PNG and saves it as an ADK session artifact.

Aang is instructed to ground all mission facts and readiness decisions in those tool results while responding as a warm, playful guide focused on learning and balance.

## Workshop extension ideas

- Add filtering by guild or required level.
- Add a tool that records completed quests and awards XP.
- Move the quest catalogue into a JSON file or database.
- Add automated tests for the quest tools.

## Security

Keep API keys and cloud credentials only in your local `.env` file or a secure secret manager. If a secret is ever committed, revoke or rotate it before removing it from Git history.
