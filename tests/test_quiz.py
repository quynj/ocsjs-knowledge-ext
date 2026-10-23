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

    async def test_passes_temperature_when_configured(self) -> None:
        await self._assert_api_request(
            api_type="chat_completions",
            expected_path="/v1/chat/completions",
            expected_payload_keys={"model", "messages", "temperature"},
            temperature=0.7,
        )

    async def _assert_api_request(
        self,
        api_type: ApiType,
        expected_path: str,
        expected_payload_keys: set[str],
        temperature: float | None = None,
    ) -> None:
        class MockResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict[str, object]:
                if api_type == "chat_completions":
                    return {"choices": [{"message": {"content": "A"}}]}
                return {"output_text": "A"}

        class MockClient:
            def __init__(self, **kwargs: object) -> None:
                type(self).last_instance = self
                self.timeout = kwargs["timeout"]
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
                    request_timeout_seconds=7,
                    temperature=temperature,
                ),
            )

        self.assertEqual(result, "A")
        client = MockClient.last_instance
        self.assertEqual(client.timeout, 7)
        self.assertEqual(client.post.call_args.args[0], f"https://example.test{expected_path}")
        self.assertEqual(set(client.post.call_args.kwargs["json"]), expected_payload_keys)
        self.assertEqual(client.post.call_args.kwargs["json"].get("temperature"), temperature)

    def test_reads_configurable_limits_timeout_and_temperature(self) -> None:
        environment = {
            "OPEN_AI_REQUEST_TIMEOUT_SECONDS": "12",
            "OPEN_AI_TEMPERATURE": "0.4",
            "MAX_TITLE_LENGTH": "1200",
            "MAX_OPTIONS_COUNT": "10",
        }
        with patch.dict(os.environ, environment):
            settings = Settings.from_env()

        self.assertEqual(settings.request_timeout_seconds, 12)
        self.assertEqual(settings.temperature, 0.4)
        self.assertEqual(settings.max_title_length, 1200)
        self.assertEqual(settings.max_options_count, 10)

    def test_rejects_option_limit_above_supported_label_count(self) -> None:
        with patch.dict(os.environ, {"MAX_OPTIONS_COUNT": "27"}):
            with self.assertRaisesRegex(ValueError, "MAX_OPTIONS_COUNT"):
                Settings.from_env()


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

    async def test_uses_configured_question_length_limit(self) -> None:
        with patch.dict(os.environ, {"MAX_TITLE_LENGTH": "4"}):
            response = await self.client.post(
                "/query", json={"title": "longer", "type": "single"}
            )
        self.assertEqual(response.json(), {"code": 40003, "message": "title too long"})

    async def test_uses_configured_option_count_limit(self) -> None:
        with patch.dict(os.environ, {"MAX_OPTIONS_COUNT": "1"}):
            response = await self.client.post(
                "/query",
                json={"title": "question", "type": "single", "options": ["one", "two"]},
            )
        self.assertEqual(response.json(), {"code": 40003, "message": "too many options"})
