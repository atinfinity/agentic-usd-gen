"""Claude API 呼び出しの共通処理。"""

from __future__ import annotations

import json
import os

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_CONTINUATIONS = 5


class LLMError(RuntimeError):
    pass


def has_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def request_json(
    *,
    model: str,
    system: str,
    content: list[dict] | str,
    schema: dict,
    tools: list[dict] | None = None,
    effort: str = "high",
) -> dict:
    """構造化出力（JSON Schema）で 1 回の応答を得る。サーバーツールの pause_turn は再開する。"""
    try:  # 使うときに読む。import だけで 1.4 秒かかり、架空の商品の生成では使わない
        import anthropic
    except ImportError as e:
        raise LLMError(f"anthropic を読み込めません: {e}") from e

    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": content}]
    params = dict(
        model=model,
        max_tokens=64000,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    if tools:
        params["tools"] = tools

    for _ in range(MAX_CONTINUATIONS + 1):
        try:  # 通信・認証・レート制限の失敗も LLMError にする（呼び出し側はそれを受けて推定に切り替える）
            with client.beta.messages.stream(messages=messages, **params) as stream:
                response = stream.get_final_message()
        except anthropic.APIError as e:
            raise LLMError(f"Claude API: {e}") from e

        if response.stop_reason == "pause_turn":
            # サーバー側ループが上限に達しただけなので、そのまま送り返して再開させる
            messages = [messages[0], {"role": "assistant", "content": response.content}]
            continue
        if response.stop_reason == "refusal":
            raise LLMError(f"Claude が応答を拒否しました: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise LLMError("max_tokens に達し、応答が途中で切れました")

        text = "".join(b.text for b in response.content if b.type == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"JSON を解釈できません: {text[:500]}") from e

    raise LLMError(f"pause_turn が {MAX_CONTINUATIONS} 回続いたため中断しました")
