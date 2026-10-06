import asyncio

from app.features.models.metering import MeteredLLMProvider, metering
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, TokenUsage


def reply(prompt: int, completion: int) -> LLMResponse:
    return LLMResponse(
        content="ok", usage=TokenUsage(prompt_tokens=prompt, completion_tokens=completion)
    )


async def test_counts_every_call_in_the_meter_including_child_tasks() -> None:
    llm = MeteredLLMProvider(ScriptedLLMProvider([reply(100, 10), reply(200, 20), reply(5, 5)]))

    with metering() as meter:
        await llm.complete([])
        await asyncio.gather(asyncio.create_task(llm.complete([])))
    await llm.complete([])  # outside the meter: not counted

    total = meter.total
    assert (total.calls, total.prompt_tokens, total.completion_tokens) == (2, 300, 30)
    assert list(meter.by_model) == ["scripted"]


async def test_parallel_meters_stay_separate() -> None:
    async def task(prompt: int) -> int:
        llm = MeteredLLMProvider(ScriptedLLMProvider([reply(prompt, 0)]))
        with metering() as meter:
            await asyncio.sleep(0)
            await llm.complete([])
        return meter.total.prompt_tokens

    assert list(await asyncio.gather(task(1), task(2))) == [1, 2]


async def test_meter_records_whether_the_founder_used_their_key() -> None:
    inner = ScriptedLLMProvider([reply(10, 2)])
    inner.own_key = True
    llm = MeteredLLMProvider(inner)
    with metering() as meter:
        await llm.complete([])
    assert meter.total.own_key is True
    assert meter.by_model["scripted"].own_key is True
