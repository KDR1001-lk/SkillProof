from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from codequest_agent import agent


class CreateMissionImageTest(IsolatedAsyncioTestCase):
    async def test_generated_image_is_saved_as_an_artifact(self) -> None:
        inline_data = SimpleNamespace(data=b"png-bytes", mime_type="image/png")
        response = SimpleNamespace(
            parts=[SimpleNamespace(inline_data=inline_data)]
        )
        models = SimpleNamespace(generate_content=AsyncMock(return_value=response))
        async_client = SimpleNamespace(models=models, aclose=AsyncMock())
        client = SimpleNamespace(aio=async_client)
        tool_context = SimpleNamespace(save_artifact=AsyncMock(return_value=0))

        with patch.object(agent.genai, "Client", return_value=client):
            result = await agent.create_mission_image(
                "Aang balancing glowing symbols above an Earth Kingdom road",
                tool_context,
                "1:1",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["artifact_version"], 0)
        self.assertEqual(result["mime_type"], "image/png")
        self.assertTrue(result["artifact_filename"].endswith(".png"))
        tool_context.save_artifact.assert_awaited_once()
        async_client.aclose.assert_awaited_once()

    async def test_empty_description_does_not_call_the_api(self) -> None:
        with patch.object(agent.genai, "Client") as client:
            result = await agent.create_mission_image(
                "   ", SimpleNamespace(), "16:9"
            )

        self.assertEqual(result["status"], "error")
        client.assert_not_called()
