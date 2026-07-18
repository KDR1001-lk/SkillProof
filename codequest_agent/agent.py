from __future__ import annotations

import os
from typing import Literal
from uuid import uuid4

import dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import types

dotenv.load_dotenv()


IMAGE_MODEL = os.getenv("CODEQUEST_IMAGE_MODEL", "gemini-3.1-flash-image")


QUESTS = [
    {
        "quest_id": "QUEST-OFFBYONE",
        "name": "The Unsteady Cabbage Cart",
        "difficulty": "novice",
        "guild": "Earth Kingdom Roads",
        "required_level": 1,
        "xp_reward": 50,
        "boss": "The Fencepost Badgermole",
        "description": (
            "A cabbage cart keeps stopping one marker too early or rolling one "
            "marker too far along an Earth Kingdom road. Steady its route and "
            "outsmart the Fencepost Badgermole by mastering loop boundaries."
        ),
        "skills_taught": ["for loops", "array indexing", "boundary conditions"],
    },
    {
        "quest_id": "QUEST-NULLSWAMP",
        "name": "The Null-Vine Marsh",
        "difficulty": "novice",
        "guild": "Water Tribe Camp",
        "required_level": 2,
        "xp_reward": 75,
        "boss": "The Vanishing Vine",
        "description": (
            "In a misty Earth Kingdom marsh, vines vanish the moment an unwary "
            "traveler grabs them. Calm the Vanishing Vine by checking every "
            "reference before relying on it."
        ),
        "skills_taught": ["null checks", "defensive programming", "error handling"],
    },
    {
        "quest_id": "QUEST-RECURSION",
        "name": "The Echoing Crystal Catacombs",
        "difficulty": "apprentice",
        "guild": "Earthbending Academy",
        "required_level": 5,
        "xp_reward": 150,
        "boss": "The Endless Echo",
        "description": (
            "Beneath the Earth Kingdom, every crystal passage opens into a copy "
            "of itself. Only a solid base case can silence the Endless Echo and "
            "lead the team back to daylight."
        ),
        "skills_taught": ["recursion", "base cases", "call stacks"],
    },
    {
        "quest_id": "QUEST-BIGO",
        "name": "The Big-O Boulder Run",
        "difficulty": "apprentice",
        "guild": "Earthbending Training Ring",
        "required_level": 6,
        "xp_reward": 175,
        "boss": "The Quadratic Quarry",
        "description": (
            "Every new input sends more boulders tumbling into the training ring. "
            "Read the pattern through the ground and tame the Quadratic Quarry "
            "with a more efficient algorithm."
        ),
        "skills_taught": ["time complexity", "algorithm analysis", "data structures"],
    },
    {
        "quest_id": "QUEST-MERGECONFLICT",
        "name": "The Great Wall Merge Crisis",
        "difficulty": "master",
        "guild": "Ba Sing Se Engineering Corps",
        "required_level": 10,
        "xp_reward": 300,
        "boss": "The Conflicting Gatekeeper",
        "description": (
            "Two engineering teams have submitted different plans for the same "
            "section of Ba Sing Se's wall. Resolve the Conflicting Gatekeeper's "
            "diffs before the city gates can open."
        ),
        "skills_taught": ["git branching", "merge conflicts", "code review"],
    },
    {
        "quest_id": "QUEST-DEADLOCK",
        "name": "The Twin-Gate Deadlock",
        "difficulty": "master",
        "guild": "Ba Sing Se Systems Bureau",
        "required_level": 12,
        "xp_reward": 350,
        "boss": "The Waiting Gatekeepers",
        "description": (
            "Two gates guard the road to the Earth King, but each gatekeeper "
            "waits for the other to unlock first. Restore movement by ordering "
            "the locks and breaking the circular wait."
        ),
        "skills_taught": ["concurrency", "locks", "deadlock avoidance"],
    },
]


def _find_quest(quest_id: str) -> dict | None:
    return next((q for q in QUESTS if q["quest_id"] == quest_id), None)


def list_quests(
    difficulty: Literal["novice", "apprentice", "master"] | None = None,
) -> dict:
    """List available quests at CodeQuest Academy, optionally filtered by difficulty.

    Args:
        difficulty: Optional quest difficulty to filter by.

    Returns:
        Matching quests and a count.
    """
    matches = []
    for quest in QUESTS:
        if difficulty and quest["difficulty"] != difficulty:
            continue
        matches.append(
            {
                "quest_id": quest["quest_id"],
                "name": quest["name"],
                "difficulty": quest["difficulty"],
                "guild": quest["guild"],
                "required_level": quest["required_level"],
                "xp_reward": quest["xp_reward"],
            }
        )
    return {"status": "success", "count": len(matches), "quests": matches}


def get_quest_details(quest_id: str) -> dict:
    """Get the full story, boss, and rewards for one quest.

    Args:
        quest_id: Quest identifier, for example QUEST-OFFBYONE.

    Returns:
        Quest details if found.
    """
    quest = _find_quest(quest_id)
    if not quest:
        return {"status": "error", "message": f"Unknown quest_id: {quest_id}"}

    return {"status": "success", "quest": quest.copy()}


def check_quest_readiness(quest_id: str, hero_level: int) -> dict:
    """Check whether a hero's level is high enough to attempt a quest.

    Args:
        quest_id: Quest identifier.
        hero_level: The adventurer's current level.

    Returns:
        Whether the hero is ready, and the level still needed if not.
    """
    quest = _find_quest(quest_id)
    if not quest:
        return {"status": "error", "message": f"Unknown quest_id: {quest_id}"}

    required_level = quest["required_level"]
    is_ready = hero_level >= required_level
    return {
        "status": "success",
        "quest_id": quest_id,
        "quest_name": quest["name"],
        "hero_level": hero_level,
        "required_level": required_level,
        "is_ready": is_ready,
        "levels_needed": max(0, required_level - hero_level),
    }


async def create_mission_image(
    description: str,
    tool_context: ToolContext,
    aspect_ratio: Literal["1:1", "4:3", "3:4", "16:9", "9:16"] = "16:9",
) -> dict:
    """Create an illustrated CodeQuest scene and save it as an ADK artifact.

    Use this only when the user explicitly asks for an image. The description
    should identify the characters, programming mission, setting, action, and
    mood to show.

    Args:
        description: A detailed description of the image the user wants.
        aspect_ratio: Output shape; 16:9 is best for scenes and 1:1 for badges.

    Returns:
        The generated artifact filename and version, or a safe error message.
    """
    clean_description = description.strip()
    if not clean_description:
        return {
            "status": "error",
            "message": "Describe the scene you want Aang to illustrate.",
        }

    prompt = (
        "Create a polished, family-friendly fantasy adventure illustration for "
        "an educational coding game called CodeQuest Academy. The visual should "
        "feel energetic, hopeful, and inspired by elemental martial-arts fantasy. "
        "Do not add logos, watermarks, captions, or UI elements. Scene request: "
        f"{clean_description}"
    )

    async_client = None
    try:
        client = genai.Client()
        async_client = client.aio
        response = await async_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size="1K",
                    output_mime_type="image/png",
                ),
            ),
        )

        image_data = None
        image_mime_type = "image/png"
        for part in response.parts or []:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                image_mime_type = part.inline_data.mime_type or image_mime_type
                break

        if image_data is None:
            return {
                "status": "error",
                "message": (
                    "The image model did not return an image. Try a different "
                    "description or check the model's safety response."
                ),
            }

        extension = "jpg" if image_mime_type == "image/jpeg" else "png"
        filename = f"codequest-{uuid4().hex[:10]}.{extension}"
        version = await tool_context.save_artifact(
            filename,
            types.Part.from_bytes(data=image_data, mime_type=image_mime_type),
            custom_metadata={
                "generator": IMAGE_MODEL,
                "aspect_ratio": aspect_ratio,
            },
        )
        return {
            "status": "success",
            "artifact_filename": filename,
            "artifact_version": version,
            "mime_type": image_mime_type,
            "aspect_ratio": aspect_ratio,
        }
    except Exception:
        return {
            "status": "error",
            "message": (
                "Image generation failed. Check your Google credentials, image "
                "model access, API quota, and ADK artifact service."
            ),
        }
    finally:
        if async_client is not None:
            try:
                await async_client.aclose()
            except Exception:
                pass


root_agent = Agent(
    name="codequest_agent",
    model="gemini-3.1-flash-lite",
    description="Aang guides CodeQuest Academy students through coding missions across the Earth Kingdom.",
    instruction="""
You are Aang, the young Avatar and guide at CodeQuest Academy. The academy is a
fan-made training ground inspired by the Earth Kingdom journey in Netflix's Avatar:
The Last Airbender Season 2. You help students master programming by completing
missions on the road to Ba Sing Se.

Speak like a warm, curious, playful, and compassionate young hero. Encourage students
to learn from mistakes, work together, and restore balance to their code. Use light
Avatar-world flavor such as balance, bending, Appa, the four elements, the Earth
Kingdom, and Ba Sing Se, but do not copy dialogue from the series. Keep every fact
about missions grounded in tool output. Do not invent mission details, rewards,
bosses, or claims about the Netflix series that the tools do not return.

Core responsibilities:
- Welcome new benders and ask their name and current training level if you don't know them yet.
- Use list_quests to show available missions, optionally filtered by difficulty (novice, apprentice, master).
- Use get_quest_details to tell the full story, boss, skills taught, and XP reward for a specific quest.
- Use check_quest_readiness before confirming an adventurer can start a quest — never guess whether they're ready.
- If a student is not ready, encourage them and tell them how many levels they still need.
- If a quest_id is not recognised, suggest calling list_quests to see valid options.
- When a student seems unsure what to do next, recommend a novice mission first.
- When a user explicitly asks for an image, use create_mission_image. Include the
  requested characters, setting, mission, action, and mood in its description.
- If the image is based on a catalogue mission, call get_quest_details first so the
  visual stays grounded in that mission's returned story, boss, and skills.
- Never claim that an image was created unless create_mission_image returns success.
  On success, tell the user the artifact filename. On error, relay its guidance.

Stay in character as Aang, but never sacrifice accuracy for flavor.
""",
    tools=[
        list_quests,
        get_quest_details,
        check_quest_readiness,
        create_mission_image,
    ],
)
