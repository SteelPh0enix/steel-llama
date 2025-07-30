import asyncio

import ollama
from discord import Member, User
from discord.ext import commands
from httpx import ConnectError

from bot import Bot, process_llm_response
from bot.chat_message import ChatMessage, MessageRole
from bot.chat_model import UnknownContextLengthValue, get_allowed_models, model_exists

LlmBackendUnavailableMessage: str = "**The LLM backend is currently unavailable, try again later.**"


def transform_mentions_into_usernames(message: str, mentions: list[User | Member]) -> str:
    for mention in mentions:
        message = message.replace(f"<@{mention.id}>", f"<@{mention.name} (UID: {mention.id})>")
    return message


class SteelLlamaCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="llm")
    async def respond(self, ctx: commands.Context):
        """Chat with the LLM

        Parameters
        ----------
        prompt : str
            Message to send.
        """
        response = await ctx.message.reply("*Starting up...*")
        user_id = ctx.message.author.id
        admin_id = self.bot.config.admin.id

        session = self.bot.get_active_user_session(user_id)
        if session is not None:
            session.add_message(
                ChatMessage.from_discord_message(ctx.message, MessageRole.USER, session.name, session.owner_id)
            )
        else:
            await response.edit(content="*Reading chat history...*")
            if self.bot.user is None:
                await response.edit(
                    content=f"*Bot is somehow not logged in, so i cannot determine which messages are mine.,. call the admin? <@{admin_id}>*"
                )
                return
            session = await self.bot.create_temporary_session(
                f"Temp-{ctx.message.channel.id}", self.bot.user.id, ctx.message.channel
            )

        if not model_exists(session.model):
            await response.edit(
                content=f"**Oops, model '{session.model}' for session '{session.name}' is not available, <@{admin_id}> fix that shit**"
            )
            return

        model_config = self.bot.config.models.find_config_for_model(session.model)

        try:
            await response.edit(content="*Processing messages...*")
            stream = await asyncio.to_thread(
                ollama.chat,
                model=session.model,
                messages=session.to_ollama_session(self.bot.config.bot.max_messages_for_context),
                stream=True,
            )
            await process_llm_response(stream, response, self.bot.config.bot, model_config)
        except ConnectError:
            await response.edit(content=LlmBackendUnavailableMessage)
        except Exception as e:
            await response.edit(content=f"**Oops, an unknown error has happened: *{str(e)}***")

        session.add_message(
            ChatMessage.from_discord_message(response, MessageRole.ASSISTANT, session.name, session.owner_id)
        )

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
            models = get_allowed_models(self.bot.config.models.excluded_models)
        except ConnectError:
            await ctx.message.reply(content=LlmBackendUnavailableMessage)
            return
        except Exception as e:
            await ctx.message.reply(content=f"**Oops, an unknown error has happened: *{str(e)}***")
            return

        formatted_message = "# Available models:\n" + "\n".join(
            f"- **{model}** - {model.parameters_size} parameters, {model.quant} quantization, {model.context_length if model.context_length != UnknownContextLengthValue else 'Unknown'} context length"
            for model in models
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
