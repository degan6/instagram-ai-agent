import json

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic import BaseModel

from instagram_ai_agent.core import llm


@pytest.fixture
def gateway(monkeypatch):
    monkeypatch.setenv('OPENROUTER_BASE_URL', 'http://gateway.test/v1/')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test-gateway')
    for kind in ('TEXT', 'JSON', 'VISION'):
        monkeypatch.setenv(f'OPENROUTER_{kind}_MODELS', 'allowed-model')
    llm._clients.clear()
    llm._cooldown.clear()
    seen = []

    def handler(request):
        assert request.url.host == 'gateway.test'
        assert request.headers['authorization'] == 'Bearer sk-test-gateway'
        body = json.loads(request.content)
        assert body['model'] == 'allowed-model'
        seen.append(body)
        message = {'role': 'assistant', 'content': '{"result":"ok"}'}
        if body.get('tools'):
            message['content'] = None
            message['tool_calls'] = [{'id': 'call_test', 'type': 'function', 'function': {
                'name': body['tools'][0]['function']['name'], 'arguments': '{"result":"ok"}'}}]
        return httpx.Response(200, json={
            'id': 'chat-test', 'object': 'chat.completion', 'created': 0,
            'model': body['model'], 'choices': [{'index': 0, 'message': message,
            'finish_reason': 'tool_calls' if body.get('tools') else 'stop'}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2},
        })

    def factory(**kwargs):
        return AsyncOpenAI(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(llm, 'AsyncOpenAI', factory)
    yield seen
    llm._clients.clear()
    llm._cooldown.clear()


@pytest.mark.asyncio
async def test_all_generation_paths_use_gateway(gateway):
    assert await llm.generate('caption', 'synthetic')
    assert (await llm.generate_json('analyze', 'synthetic'))['result'] == 'ok'
    class Result(BaseModel):
        result: str
    assert (await llm.generate_json_model('analyze', 'synthetic', Result)).result == 'ok'
    assert await llm.describe_image('data:image/png;base64,AAAA')
    assert len(gateway) == 4


def test_endpoint_override_resolved_after_import(monkeypatch):
    monkeypatch.setenv('OPENROUTER_BASE_URL', 'http://late.test/v1/')
    assert llm.openrouter_base_url() == 'http://late.test/v1'


def test_default_routes_preserved(monkeypatch):
    monkeypatch.delenv('OPENROUTER_TEXT_MODELS', raising=False)
    monkeypatch.delenv('OPENROUTER_BASE_URL', raising=False)
    assert llm._configured_chain(llm.CAPTION_CHAIN, 'TEXT') is llm.CAPTION_CHAIN
    assert llm.openrouter_base_url() == 'https://openrouter.ai/api/v1'


def test_empty_override_fails_closed(monkeypatch):
    monkeypatch.setenv('OPENROUTER_JSON_MODELS', ' , ')
    with pytest.raises(ValueError):
        llm._configured_chain(llm.JSON_CHAIN, 'JSON')


def test_gateway_setup_validation_stays_on_gateway(monkeypatch):
    from instagram_ai_agent import cli
    monkeypatch.setenv('OPENROUTER_BASE_URL', 'http://gateway.test/v1')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test-gateway')
    def get(url, **kwargs):
        assert url == 'http://gateway.test/v1/models'
        assert kwargs['headers']['Authorization'] == 'Bearer sk-test-gateway'
        return httpx.Response(200, json={'data': [{'id': 'allowed-model'}]})
    monkeypatch.setattr(httpx, 'get', get)
    assert cli._setup_get_openrouter_key() == 'sk-test-gateway'


@pytest.mark.asyncio
async def test_budget_denial_never_uses_public_endpoint(monkeypatch):
    monkeypatch.setenv('OPENROUTER_BASE_URL', 'http://gateway.test/v1')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test-gateway')
    monkeypatch.setenv('OPENROUTER_TEXT_MODELS', 'first,second')
    llm._clients.clear()
    llm._cooldown.clear()
    seen = []
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(429, json={'error': {'message': 'Budget exceeded', 'type': 'budget_exceeded'}})
    monkeypatch.setattr(llm, 'AsyncOpenAI', lambda **kw: AsyncOpenAI(
        **kw, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ))
    with pytest.raises(llm.AllProvidersFailed):
        await llm.generate('caption', 'synthetic')
    assert len(seen) == 2
    assert all(url == 'http://gateway.test/v1/chat/completions' for url in seen)
    llm._clients.clear()
    llm._cooldown.clear()
