from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import ollama

from bot.configuration import ModelConfig, ModelsConfig


def split_model_name(full_name: str) -> tuple[str | None, str | None]:
    name_split = full_name.split(":")
    if len(name_split) == 2:
        return name_split[0], name_split[1]
    if len(name_split) == 1:
        return name_split[0] if name_split[0] else None, None
    return None, None


@dataclass
class ChatModel:
    name: str | None
    tag: str | None
    size: str | None
    parameters_size: str | None
    quant: str | None
    context_length: int | None
    config: ModelConfig

    @staticmethod
    def from_ollama_model(ollama_model: ollama.ListResponse.Model, model_config: ModelConfig) -> ChatModel:
        def find_context_length(info: Mapping[str, Any]) -> int | None:
            for key, value in info.items():
                if key.endswith("context_length"):
                    return value
            return None

        if ollama_model.model is None:
            raise ValueError("Error: model cannot be nameless!")

        full_name: str = ollama_model.model
        name: str | None = full_name
        tag: str | None = None
        ctx_length: int | None = None
        size: str | None = None

        # get model name/context length from ollama
        if full_name is not None:
            model_info = ollama.show(full_name)
            if model_info.modelinfo is not None:
                ctx_length = find_context_length(model_info.modelinfo)
            name, tag = split_model_name(full_name)

        if ollama_model.size is not None:
            size = ollama_model.size.human_readable()

        # override the context length if present in config
        if model_config.context_limit is not None:
            ctx_length = model_config.context_limit

        if (details := ollama_model.details) is not None:
            return ChatModel(
                name=name,
                tag=tag,
                size=size,
                parameters_size=details.parameter_size,
                quant=details.quantization_level,
                context_length=ctx_length,
                config=model_config,
            )

        return ChatModel(
            name=name,
            tag=tag,
            size=size,
            parameters_size=None,
            quant=None,
            context_length=ctx_length,
            config=model_config,
        )


def get_all_models(configs: ModelsConfig) -> list[ChatModel]:
    models: list[ChatModel] = []
    for model in ollama.list().models:
        model_name = model.model if model.model is not None else ""
        if (model_config := configs.models.get(model_name, None)) is not None:
            models.append(ChatModel.from_ollama_model(model, model_config))
    return models


def get_model(name: str, configs: ModelsConfig) -> ChatModel | None:
    for model in ollama.list().models:
        model_name = model.model if ((model.model is not None) and model.model.startswith(name)) else ""
        if (model_config := configs.models.get(model_name, None)) is not None:
            return ChatModel.from_ollama_model(model, model_config)
    return None
