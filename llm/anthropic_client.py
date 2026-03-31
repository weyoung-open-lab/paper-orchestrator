# paper_agent/llm/anthropic_client.py
from __future__ import annotations

import os
import base64
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

import anthropic


@dataclass
class LLMConfig:
    """LLM call configuration (no paper logic)."""
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.4
    max_tokens: int = 4000
    max_continue_rounds: int = 3


class AnthropicClient:
    """
    Thin wrapper around Anthropic SDK:
      - send prompt
      - optionally attach images
      - handle continuation when truncated (best effort)
    Does NOT know paper structure.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, cfg: Optional[LLMConfig] = None):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Missing API key. Provide api_key or set ANTHROPIC_API_KEY.")

        base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        self.cfg = cfg or LLMConfig()

        if base_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        system: str,
        user: str,
        image_paths: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Return text output. If the model output is likely truncated, try to continue a few rounds.
        """
        max_tokens = max_tokens or self.cfg.max_tokens
        temperature = temperature if temperature is not None else self.cfg.temperature

        messages = [self._build_user_message(user, image_paths=image_paths)]
        text, stop_reason = self._call(system, messages, max_tokens=max_tokens, temperature=temperature)

        # Best-effort continuation if truncated
        rounds = 0
        while self._needs_continue(stop_reason) and rounds < self.cfg.max_continue_rounds:
            rounds += 1
            cont_user = "Continue from where you left off. Do not repeat previous text."
            messages.append({"role": "assistant", "content": [{"type": "text", "text": text}]})
            messages.append({"role": "user", "content": [{"type": "text", "text": cont_user}]})
            more, stop_reason = self._call(system, messages, max_tokens=max_tokens, temperature=temperature)
            if not more.strip():
                break
            text = (text.rstrip() + "\n" + more.lstrip()).strip()

        return text.strip()

    def _call(self, system: str, messages: List[Dict[str, Any]], max_tokens: int, temperature: float) -> Tuple[str, Optional[str]]:
        resp = self.client.messages.create(
            model=self.cfg.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        out = ""
        for c in getattr(resp, "content", []) or []:
            # SDK returns content blocks
            if getattr(c, "type", None) == "text":
                out += c.text
            elif isinstance(c, dict) and c.get("type") == "text":
                out += c.get("text", "")
        stop_reason = getattr(resp, "stop_reason", None)
        return out, stop_reason

    def _needs_continue(self, stop_reason: Optional[str]) -> bool:
        # Anthropic commonly uses "max_tokens" when hitting the token limit
        return stop_reason in ("max_tokens",)

    def _build_user_message(self, user_text: str, image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        blocks: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]
        if image_paths:
            for p in image_paths:
                img_block = self._image_block_from_path(p)
                if img_block:
                    blocks.append(img_block)
        return {"role": "user", "content": blocks}

    def _image_block_from_path(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            if not path or not os.path.exists(path):
                return None
            ext = os.path.splitext(path)[1].lower()
            mime = "image/png"
            if ext in (".jpg", ".jpeg"):
                mime = "image/jpeg"
            elif ext == ".webp":
                mime = "image/webp"

            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

            return {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}}
        except Exception:
            return None
