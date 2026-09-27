# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from pydantic import Field

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.llm import LLMProviderInfo
from nat.cli.register_workflow import register_llm_client
from nat.cli.register_workflow import register_llm_provider
from nat.data_models.common import OptionalSecretStr
from nat.data_models.common import get_secret_value
from nat.data_models.llm import LLMBaseConfig

logger = logging.getLogger(__name__)


class FallbackNIMModelConfig(LLMBaseConfig, name="fallback_nim"):
    """
    NVIDIA NIM model configuration with primary model and automatic fallback chain.
    """
    primary_model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b",
        description="The primary NVIDIA NIM model name.",
    )
    fallback_models: list[str] = Field(
        default_factory=lambda: [
            "nvidia/nemotron-3-super-120b-a12b",
            "openai/gpt-oss-20b",
            "meta/muse-glimmer-30b",
            "meta/llama-3.2-11b-vision-instruct",
        ],
        description="List of fallback models to try in sequential order if primary fails.",
    )
    base_url: str | None = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL for NVIDIA NIM endpoint.",
    )
    api_key: OptionalSecretStr = Field(
        default=None,
        description="NVIDIA API Key (defaults to NVIDIA_API_KEY environment variable).",
    )
    temperature: float | None = Field(
        default=0.0,
        description="Sampling temperature.",
    )
    max_tokens: int = Field(
        default=512,
        description="Maximum tokens to generate.",
    )


@register_llm_provider(config_type=FallbackNIMModelConfig)
async def fallback_nim_provider(
    llm_config: FallbackNIMModelConfig,
    _builder: Builder,
) -> AsyncIterator[LLMProviderInfo]:
    """Registers fallback_nim provider with NAT."""
    yield LLMProviderInfo(
        config=llm_config,
        description="NVIDIA NIM model with automatic sequential fallback chain.",
    )


@register_llm_client(config_type=FallbackNIMModelConfig, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
async def fallback_nim_langchain(
    llm_config: FallbackNIMModelConfig,
    _builder: Builder,
) -> AsyncIterator[Any]:
    """Constructs a LangChain ChatNVIDIA runnable with automatic fallbacks."""
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    api_key = get_secret_value(llm_config.api_key) or os.getenv("NVIDIA_API_KEY")
    base_url = llm_config.base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    logger.info(
        "Configuring Primary Model: %s with Fallbacks: %s",
        llm_config.primary_model,
        llm_config.fallback_models,
    )

    primary = ChatNVIDIA(
        model=llm_config.primary_model,
        api_key=api_key,
        base_url=base_url,
        max_completion_tokens=llm_config.max_tokens,
        temperature=llm_config.temperature,
    )

    fallbacks = [
        ChatNVIDIA(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            max_completion_tokens=llm_config.max_tokens,
            temperature=llm_config.temperature,
        )
        for model_name in llm_config.fallback_models
    ]

    client = primary.with_fallbacks(fallbacks)
    yield client
