from discord.ext import commands
import asyncio
import ollama
from bot import Bot, process_llm_response


class BotCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="llm", description="Interact with the LLM using a prompt.")
    async def respond(self, ctx: commands.Context, *, prompt):
        model = self.bot.config.models.default_model
        message = await ctx.message.reply("*Processing...*")

        try:
            stream = await asyncio.to_thread(
                ollama.generate, model, prompt, stream=True
            )

            await process_llm_response(stream, message, self.bot.config)
        except Exception as e:
            await message.edit(content=f"Error: {str(e)}")

    @commands.command(
        name="llm-new-session", description="Create a new private session."
    )
    async def llm_new_session(self, ctx: commands.Context, session_name: str | None):
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        await ctx.send(
            f"*Created new session called {session_name}, and switched to it*"
        )

    @commands.command(name="llm-list-sessions", description="List all saved sessions.")
    async def llm_list_sessions(self, ctx):
        # Placeholder logic
        await ctx.send("Listing sessions...")

    @commands.command(
        name="llm-change-session", description="Switch to a different session."
    )
    async def llm_change_session(self, ctx: commands.Context, session_name: str | None):
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Switched to session {session_name}*")

    @commands.command(name="llm-remove-session", description="Remove a saved session.")
    async def llm_remove_session(self, ctx: commands.Context, session_name: str | None):
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Removed session {session_name}*")

    @commands.command(
        name="llm-get-session-size", description="Get the size of a saved session."
    )
    async def llm_get_session_size(
        self, ctx: commands.Context, session_name: str | None
    ):
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        # Placeholder logic
        await ctx.send(f"*Session {session_name} size: 1024 bytes*")

    @commands.command(
        name="llm-set-system-prompt",
        description="Set a system prompt for the current session.",
    )
    async def llm_set_system_prompt(
        self, ctx: commands.Context, prompt_content: str | None
    ):
        if prompt_content is None:
            await ctx.send("Missing prompt content!")
            return

        # Placeholder logic
        await ctx.send(f"*System prompt set to: {prompt_content}*")

    @commands.command(name="llm-list-models", description="List all available models.")
    async def llm_list_models(self, ctx):
        # Placeholder logic
        await ctx.send("Listing models...")

    @commands.command(
        name="llm-set-session-model", description="Set a model for the current session."
    )
    async def llm_set_session_model(
        self, ctx: commands.Context, session_name: str | None, model_name: str | None
    ):
        if session_name is None or model_name is None:
            await ctx.send("Missing session name or model name!")
            return

        # Placeholder logic
        await ctx.send(f"*Session {session_name} set to use model {model_name}*")


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
