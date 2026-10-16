from __future__ import annotations
import os
import logging
from typing import Optional
from django.conf import settings

from .exceptions import (
    AITutorException,
    MissingCredentialsError,
    ProviderAuthenticationError,
    ProviderQuotaExceededError,
    ProviderTimeoutError
)

logger = logging.getLogger(__name__)


class AIProviderClient:
    """
    Unified provider client supporting Google GenAI and OpenAI SDKs
    with strict timeout control, bounded output limits, and safe error mapping.
    """

    def __init__(self):
        self.api_key = (
            getattr(settings, 'AI_TUTOR_API_KEY', None)
            or os.environ.get('AI_TUTOR_API_KEY')
            or os.environ.get('OPENAI_API_KEY')
            or os.environ.get('GEMINI_API_KEY')
            or ''
        ).strip()

        configured_provider = getattr(settings, 'AI_TUTOR_PROVIDER', 'auto').lower()
        self.timeout = getattr(settings, 'AI_TUTOR_TIMEOUT_SECONDS', 30)
        self.max_output_tokens = getattr(settings, 'AI_TUTOR_MAX_OUTPUT_TOKENS', 2048)

        # Detect provider: Gemini keys start with AQ. or AIza, OpenAI keys start with sk-
        if configured_provider == 'gemini':
            self.provider = 'gemini'
        elif configured_provider == 'openai':
            self.provider = 'openai'
        else:
            if self.api_key.startswith('AQ.') or self.api_key.startswith('AIza'):
                self.provider = 'gemini'
            elif self.api_key.startswith('sk-'):
                self.provider = 'openai'
            else:
                self.provider = 'gemini'

        if self.provider == 'gemini':
            self.model_name = getattr(settings, 'AI_TUTOR_MODEL', None) or 'gemini-3.8-flash'
        else:
            self.model_name = getattr(settings, 'OPENAI_MODEL', None) or getattr(settings, 'AI_TUTOR_MODEL', 'gpt-4o-mini')

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, system_instruction: str, user_prompt: str) -> dict:
        """
        Sends system instructions and user prompt to configured provider.
        """
        if not self.is_configured():
            raise MissingCredentialsError()

        if self.provider == 'gemini':
            return self._generate_gemini(system_instruction, user_prompt)
        else:
            return self._generate_openai(system_instruction, user_prompt)

    def _generate_gemini(self, system_instruction: str, user_prompt: str, retries_left: int = 2) -> dict:
        import time
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=self.max_output_tokens,
                temperature=0.3,
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )

            text = response.text or ""
            # Estimate tokens if metadata is not provided
            tokens = getattr(response, 'usage_metadata', None)
            tokens_count = tokens.total_token_count if tokens else len(text.split())

            return {
                'text': text,
                'tokens_used': tokens_count,
                'model': self.model_name,
                'provider': 'gemini'
            }

        except Exception as ex:
            err_str = str(ex).lower()
            err_name = type(ex).__name__
            logger.error(f"Gemini API error ({err_name}): {ex}")

            # Handle transient 503 / high demand spikes with bounded retry
            if ("503" in err_str or "unavailable" in err_str or "servererror" in err_name.lower()) and retries_left > 0:
                logger.info(f"Transient Gemini 503 encountered, retrying in 2s ({retries_left} attempts left)...")
                time.sleep(2.0)
                return self._generate_gemini(system_instruction, user_prompt, retries_left=retries_left - 1)

            if "401" in err_str or "unauthenticated" in err_str or "invalid_api_key" in err_str:
                raise ProviderAuthenticationError()
            elif "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                raise ProviderQuotaExceededError()
            elif "timeout" in err_str or "deadline" in err_str:
                raise ProviderTimeoutError()
            elif "404" in err_str and "not found" in err_str:
                # If configured model is deprecated, try fallback to gemini-3.8-flash
                if self.model_name != "gemini-3.8-flash":
                    logger.warning(f"Retrying with gemini-3.8-flash fallback due to: {ex}")
                    try:
                        self.model_name = "gemini-3.8-flash"
                        return self._generate_gemini(system_instruction, user_prompt, retries_left=0)
                    except Exception:
                        pass
                raise AITutorException(f"Configured model '{self.model_name}' was not found. Please update AI_TUTOR_MODEL.")
            else:
                raise AITutorException(f"AI service encountered a temporary error: {str(ex)[:150]}")


    def _generate_openai(self, system_instruction: str, user_prompt: str) -> dict:
        try:
            from openai import OpenAI
            from openai.types.chat import ChatCompletionMessageParam

            client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ]

            resp = client.chat.completions.create(
                model=str(self.model_name),
                messages=messages,
                max_tokens=int(self.max_output_tokens),
                temperature=0.3
            )

            content = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else len(content.split())

            return {
                'text': content,
                'tokens_used': tokens,
                'model': self.model_name,
                'provider': 'openai'
            }

        except Exception as ex:
            err_name = type(ex).__name__
            logger.error(f"OpenAI API error ({err_name}): {ex}")

            if "AuthenticationError" in err_name or "invalid_api_key" in str(ex):
                raise ProviderAuthenticationError()
            elif "RateLimitError" in err_name or "quota" in str(ex).lower():
                raise ProviderQuotaExceededError()
            elif "APITimeoutError" in err_name or "timeout" in str(ex).lower():
                raise ProviderTimeoutError()
            else:
                raise AITutorException(f"AI service error: {str(ex)[:150]}")
