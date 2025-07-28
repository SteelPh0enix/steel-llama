import asyncio

import ollama
from discord.ext import commands
from discord import User, Member
from httpx import ConnectError

from bot import Bot, process_llm_response
from bot.model import Model, UnknownContextLengthValue

LlmBackendUnavailableMessage: str = "**The LLM backend is currently unavailable, try again later.**"


def translate_mentions_into_usernames(message: str, mentions: list[User | Member]) -> str:
    for mention in mentions:
        message = message.replace(
            f"<@{mention.id}>", f"<@{mention.name if mention.name is not None else 'Unknown user'}>"
        )
    return message


class SteelLlamaCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="llm")
    async def respond(self, ctx: commands.Context, *, prompt: str | None):
        """Chat with the LLM

        Parameters
        ----------
        prompt : str
            Message to send.
        """
        if prompt is None:
            await ctx.message.reply("*Error: no message, what do you want me to respond to?*")
            return

        prompt = translate_mentions_into_usernames(prompt, ctx.message.mentions)
        print(f"Responding to {prompt}")

        model = (
            self.bot.config.models.default_model
        )  # TODO: use model selected by the user (add persistent user config first)
        message = await ctx.message.reply("*Processing...*")
        model_config = self.bot.config.models.find_config_for_model(model)

        try:
            stream = await asyncio.to_thread(ollama.generate, model, prompt, stream=True)

            await process_llm_response(stream, message, self.bot.config.bot, model_config)
        except ConnectError:
            await message.edit(content=LlmBackendUnavailableMessage)
        except Exception as e:
            await message.edit(content=f"**Oops, an unknown error has happened: *{str(e)}***")

    @commands.command(name="llm-new-session")
    async def llm_new_session(self, ctx: commands.Context, session_name: str | None):
        """Create a new private session.

        Parameters
        ----------
        session_name : str | None
            The name of the session to create. Must not be None.
        """
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        await ctx.send(f"*Created new session called {session_name}, and switched to it*")

    @commands.command(name="llm-list-sessions")
    async def llm_list_sessions(self, ctx: commands.Context):
        """List all saved sessions."""
        # Placeholder logic
        await ctx.send("Listing sessions...")

    @commands.command(name="llm-change-session")
    async def llm_change_session(self, ctx: commands.Context, session_name: str | None):
        """Switch to a different session.

        Parameters
        ----------
        session_name : str | None
            The name of the session to switch to. Must not be None.
        """
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Switched to session {session_name}*")

    @commands.command(name="llm-remove-session")
    async def llm_remove_session(self, ctx: commands.Context, session_name: str | None):
        """Remove a saved session.

        Parameters
        ----------
        session_name : str | None
            The name of the session to remove. Must not be None.
        """
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Removed session {session_name}*")

    @commands.command(name="llm-get-session-size")
    async def llm_get_session_size(self, ctx: commands.Context, session_name: str | None):
        """Get the size of a saved session.

        Parameters
        ----------
        session_name : str | None
            The name of the session to check. Must not be None.
        """
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Session {session_name} size: 1024 bytes*")

    @commands.command(name="llm-set-system-prompt")
    async def llm_set_system_prompt(self, ctx: commands.Context, prompt_content: str | None):
        """Set a system prompt for the current session.

        Parameters
        ----------
        prompt_content : str | None
            The content of the new system prompt. Must not be None.
        """
        if prompt_content is None:
            await ctx.send("Missing prompt content!")
            return

        # Placeholder logic
        await ctx.send(f"*System prompt set to: {prompt_content}*")

    @commands.command(name="llm-list-models")
    async def llm_list_models(self, ctx: commands.Context):
        """List all available models."""
        try:
            models = [Model.from_ollama_model(model) for model in ollama.list().models]
        except ConnectError:
            await ctx.message.reply(content=LlmBackendUnavailableMessage)
            return
        except Exception as e:
            await ctx.message.reply(content=f"**Oops, an unknown error has happened: *{str(e)}***")
            return

        excluded_models = self.bot.config.models.excluded_models
        allowed_models = [model for model in models if model.name not in excluded_models]

        formatted_message = "# Available models:\n" + "\n".join(
            f"- **{model}** - {model.parameters_size} parameters, {model.quant} quantization, {model.context_length if model.context_length != UnknownContextLengthValue else 'Unknown'} context length"
            for model in allowed_models
        )

        await ctx.message.reply(formatted_message)

    @commands.command(name="llm-set-session-model")
    async def llm_set_session_model(self, ctx: commands.Context, session_name: str | None, model_name: str | None):
        """Set a model for the current session.

        Parameters
        ----------
        session_name : str | None
            The name of the session to update. Must not be None.
        model_name : str | None
            The name of the model to assign. Must not be None.
        """
        if session_name is None or model_name is None:
            await ctx.send("Missing session name or model name!")
            return

        # Placeholder logic
        await ctx.send(f"*Session {session_name} set to use model {model_name}*")


async def setup(bot):
    await bot.add_cog(SteelLlamaCommands(bot))
