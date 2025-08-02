from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import ollama

from bot.configuration import ModelConfig, ModelsConfig

UnknownFieldValue: str = "Unknown"
UnknownContextLengthValue: int = -1


def find_context_length(info: Mapping[str, Any]) -> int:
    for key, value in info.items():
        if key.endswith("context_length"):
            return value
    return UnknownContextLengthValue


@dataclass
class ChatModel:
    name: str
    tag: str
    size: str
    parameters_size: str
    quant: str
    context_length: int

    @staticmethod
    def from_ollama_model(ollama_model: ollama.ListResponse.Model, model_config: ModelConfig) -> ChatModel:
        name = ollama_model.model if ollama_model.model is not None else UnknownFieldValue
        tag = UnknownFieldValue
        ctx_length = UnknownContextLengthValue

        if name != UnknownFieldValue:
            model_info = ollama.show(name)
            if model_info.modelinfo is not None:
                ctx_length = find_context_length(model_info.modelinfo)

        if model_config.context_limit is not None:
            ctx_length = model_config.context_limit

        name_split = name.split(":")
        if len(name_split) == 2:
            name, tag = name_split[0], name_split[1]

        size = ollama_model.size.human_readable() if ollama_model.size is not None else UnknownFieldValue

        if (details := ollama_model.details) is not None:
            parameters = details.parameter_size if details.parameter_size is not None else UnknownFieldValue
            quant = details.quantization_level if details.quantization_level is not None else UnknownFieldValue

            return ChatModel(
                name=name,
                tag=tag,
                size=size,
                parameters_size=parameters,
                quant=quant,
                context_length=ctx_length,
            )

        return ChatModel(
            name=name,
            tag=tag,
            size=size,
            parameters_size=UnknownFieldValue,
            quant=UnknownFieldValue,
            context_length=ctx_length,
        )

    def __str__(self) -> str:
        return self.name


def get_all_models(configs: ModelsConfig) -> list[ChatModel]:
    models: list[ChatModel] = []
    for model in ollama.list().models:
        model_name = model.model if model.model is not None else ""
        if (model_config := configs.get_model_config(model_name)) is not None:
            models.append(ChatModel.from_ollama_model(model, model_config))
    return models


def get_model(name: str, configs: ModelsConfig) -> ChatModel | None:
    for model in ollama.list().models:
        model_name = model.model if model.model is not None else ""
        if (model_config := configs.get_model_config(model_name)) is not None:
            return ChatModel.from_ollama_model(model, model_config)
    return None
