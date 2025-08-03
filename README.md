# steel-llama

My Discord bot (update of unreasonable-llama-discord for Ollama)

This bot is a bridge between Discord and Ollama, with it's own user and session management system.

## Features

- By default, the bot uses the recent chat history as context. Amount of messages stored in context depends on maximum context size and bot's configuration.
- Sessions are stored in bot's database and active session can be selected by the user via bot commands.
- Users can start their own, private sessions that contain only the conversation between them and the bot. Sessions are identified by IDs provided by the user.
- Sessions are bound to user ID
- Users can delete their private sessions (as whole)
- Users can select the model for each session. Default model is configured by bot's administrator.
- Users can set the system prompt for each session.

The bot uses local sqlite3 database to store the data.
Configuration is stored in configparser-compatible .ini file.

## Bot commands

Commands can be triggered by starting the message with bot's prefix, followed by command name and arguments.
For the sake of following examples, `$` is the bot's command prefix, and `@username` is the username.
Bot should respond to the message that triggered the command. If the command name is unknown, bot will not respond.

### Trigger bot response

```text
$llm what's the capital of Poland?
```

Example bot's response:

```text
The capital of Poland is Warsaw.
```

### Show bot's help

```text
$help
```

Bot's response:

```text
SteelLlamaCommands:
  llm                   Chat with the LLM
  llm-change-session    Switch to a different session.
  llm-get-session-size  Get the size of a saved session.
  llm-list-models       List all available models.
  llm-list-sessions     List all saved sessions.
  llm-new-session       Create a new private session.
  llm-remove-session    Remove a saved session.
  llm-set-session-model Set a model for the current session.
  llm-set-system-prompt Set a system prompt for the current session.
​No Category:
  help                  Shows this message

Type $help command for more info on a command.
You can also type $help category for more info on a category.
```

### Create new session

```text
$llm-new-session MyCustomSession
```

Bot's response:

```text
*Created and switched to MyCustomSession*
```

### List available sessions

```text
$llm-list-sessions
```

Bot's response:

```text
List of your sessions:
- MyCustomSession (model: SomeModel)
- OtherSession (model: SomeOtherModel)
```

### Change current session

```text
$llm-change-session OtherSession
```

Bot's response:

```text
Changed your session to OtherSession
```

To switch to global session, use `global` as the name. You cannot create a session with this name.

### Remove a session

```text
$llm-remove-session OtherSession
```

Bot's response:

```text
Removed session OtherSession
```

If current session is removed, bot will fallback to global session.
In that case, the response will be:

```text
Removed current session OtherSession, switching to global session.
```

### Check current session size

```text
$llm-get-session-size MyCustomSession
```

Bot's response:

```text
Session MyCustomSession currently contains 1024 tokens.
```

### Set system prompt for current session

```text
$llm-set-system-prompt You are a helpful assistant.
```

Bot's response:

```text
Changed system prompt for current session to `You are a helpful assistant.`
```

### List available models

```text
$llm-list-models
```

Bot's response:

```text
Available models:
- ModelAName - 8B parameters, Q6_K quantization
- ModelBName - 14B parameters, Q4_K_XL quantization
- ModelCName - 4B parameters, Q8_0 quantization
```

Models must be defined in configuration file, see [Configuration file](#configuration-file) section.

### Set model for a session

```text
$llm-set-session-model MyCustomSession ModelCName
```

Bot's response:

```text
Changed model for session MyCustomSession to ModelCName (4B parameters, Q8_0 quantization)
```

Model for global session is stored in bot's [configuration file](#configuration-file).

## Configuration file

```ini
[models]
# The model to use by default
default_model = qwen3-8b

[admin]
# Discord ID of administrator's account.
id = 12345

[bot]
# Discord API key for the bot
discord_api_key = your_discord_api_key_here
# Prefix for bot commands
bot_prefix = $
# Delay in seconds between message edits
edit_delay_seconds = 0.5
# Maximum number of messages to use for context
max_messages_for_context = 30
# Path to sessions database
session_db_path = ./bot.db
# Default system prompt for all sessions
default_system_prompt = You are SteelLlama, an LLM-powered Discord bot, proceed with the following conversation with the users. Every message is prefixed with a line containing the username of sender (prefixed with @). DO NOT add that prefix to your messages, use it only to identify the authors. Messages directed specifically to you are prefixed with "$llm".

# Every supported model must have a section in configuration
[models.qwen3-8b]
# Optional prefix and suffix for thinking indicator (used for models like qwen3)
thinking_prefix = "<think>"
thinking_suffix = "</think>"
# Best to provide name/path to `transformers`-compatible tokenizer for precise token counting
tokenizer = Qwen/Qwen3-8B 
# Context limit is optional, by default the one reported by ollama is used
context_limit = 65536
```

## Operations

This section contains information about internal workings of the bot, for documentation and vibecoding purposes.
