from discord.ext import commands


class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="llm")
    async def respond(self, ctx):
        await ctx.send("lol, lmao")

    @commands.command(name="llm-help")
    async def llm_help(self, ctx):
        """Display available commands."""
        await ctx.send(
            "**This is SteelLlama, simple bridge between Ollama and Discord with user/session management.**\n"
            "Available commands:\n"
            "- $llm-new-session [session name]\n"
            "- $llm-list-sessions\n"
            "- $llm-change-session [session name]\n"
            "- $llm-remove-session [session name]\n"
            "- $llm-get-session-size [session name]\n"
            "- $llm-set-system-prompt [prompt content]\n"
            "- $llm-list-models\n"
            "- $llm-set-session-model [session-name] [model name]"
        )

    @commands.command(name="llm-new-session")
    async def llm_new_session(self, ctx, session_name: str | None):
        """Create a new private session."""
        if session_name is None:
            await ctx.send("Missing session name!")
            return

        await ctx.send(
            f"*Created new session called {session_name}, and switched to it*"
        )

    # Add more commands here as needed
    # e.g., list-sessions, change-session, etc.


async def setup(bot):
    await bot.add_cog(BotCommands(bot))
