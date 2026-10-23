import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.config import ApiType, Settings
from app.llm import _response_text, answer
from app.main import app
from app.models import OptionObject
from app.parsing import parse_answer


class ParseAnswerTests(unittest.TestCase):
    def test_parses_single_choice(self) -> None:
        self.assertEqual(parse_answer("答案：B", "single", ["first", "second"]), "B")

    def test_ignores_choice_letters_inside_explanatory_words(self) -> None:
        self.assertEqual(
            parse_answer("The answer is A.", "single", ["first", "second"]),
            "A",
        )

    def test_parses_multiple_choice_as_hash_separated_labels(self) -> None:
        self.assertEqual(
            parse_answer("A、C", "multiple", ["first", "second", "third"]),
            "A#C",
        )

    def test_parses_judgment(self) -> None:
        self.assertEqual(parse_answer("错误", "judgement", None), "错误")

    def test_parses_negated_judgment(self) -> None:
        self.assertEqual(parse_answer("这个说法不对", "judge", None), "错误")

    def test_rejects_multiple_answers_for_single_choice(self) -> None:
        with self.assertRaises(ValueError):
            parse_answer("A,C", "single", ["first", "second", "third"])

    def test_uses_custom_option_labels(self) -> None:
        options = [OptionObject(label="C", text="third")]
        self.assertEqual(parse_answer("C", "single", options), "C")


class ModelResponseTests(unittest.TestCase):
    def test_extracts_chat_completion_text(self) -> None:
        payload = {"choices": [{"message": {"content": " A "}}]}
        self.assertEqual(_response_text(payload, "chat_completions"), "A")

    def test_extracts_responses_api_output_text(self) -> None:
        payload = {"output": [{"content": [{"type": "output_text", "text": " A "}]}]}
        self.assertEqual(_response_text(payload, "responses"), "A")


class ModelRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_chat_completions_endpoint(self) -> None:
        await self._assert_api_request(
            api_type="chat_completions",
            expected_path="/v1/chat/completions",
            expected_payload_keys={"model", "messages"},
        )

    async def test_uses_responses_endpoint(self) -> None:
        await self._assert_api_request(
            api_type="responses",
            expected_path="/v1/responses",
            expected_payload_keys={"model", "instructions", "input"},
        )

    async def _assert_api_request(
        self, api_type: ApiType, expected_path: str, expected_payload_keys: set[str]
    ) -> None:
        class MockResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict[str, object]:
                if api_type == "chat_completions":
                    return {"choices": [{"message": {"content": "A"}}]}
                return {"output_text": "A"}

        class MockClient:
            def __init__(self, **_: object) -> None:
                type(self).last_instance = self
                self.post = AsyncMock(return_value=MockResponse())

            async def __aenter__(self) -> "MockClient":
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

        with patch("app.llm.httpx.AsyncClient", MockClient):
            result = await answer(
                "system",
                "question",
                Settings(
                    api_key="test-key",
                    base_url="https://example.test/v1",
                    model="test-model",
                    api_type=api_type,
                ),
            )

        self.assertEqual(result, "A")
        client = MockClient.last_instance
        self.assertEqual(client.post.call_args.args[0], f"https://example.test{expected_path}")
        self.assertEqual(set(client.post.call_args.kwargs["json"]), expected_payload_keys)


class QueryEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )
        self.environment = patch.dict(
            os.environ,
            {"OPEN_AI_API_KEY": "test-key", "OPEN_AI_MODEL": "test-model"},
        )
        self.environment.start()

    async def asyncTearDown(self) -> None:
        self.environment.stop()
        await self.client.aclose()

    async def test_single_choice_get_contract(self) -> None:
        with patch("app.main.answer", new=AsyncMock(return_value="B")):
            response = await self.client.get(
                "/query",
                params={"title": "question", "type": "single", "options": '["one","two"]'},
            )
        self.assertEqual(
            response.json(),
            {"code": 0, "data": {"answer": "B", "question": "question", "ai": True}},
        )

    async def test_multiple_choice_post_contract(self) -> None:
        with patch("app.main.answer", new=AsyncMock(return_value="A,C")):
            response = await self.client.post(
                "/query",
                json={"title": "question", "type": "multiple", "options": ["one", "two", "three"]},
            )
        self.assertEqual(response.json()["data"]["answer"], "A#C")

    async def test_unknown_question_type_returns_error(self) -> None:
        response = await self.client.post(
            "/query", json={"title": "question", "type": "fill"}
        )
        self.assertEqual(response.json()["code"], 40001)
