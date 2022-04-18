# Akyuu Bot - The Touhoumon Revised Discord Bot

## Features

On the user end:

- A Pokemon rom parser that parses specific data to use for the bot
    - This includes (but is not limited to):
        - Base Stats
        - Specie names
        - Dex entries
        - Level up movesets
        - Abilities
        - Locations in the wild
- A bot that provides a simple interface to this data to allow users to quickly look up the information they need using
  modern Discord features such as slash commands, modals, ephemeral responses, context commands, and selection menus
- A lot of configuration options to make sure the bot can be accurate through updates
    - May support any Pokemon Fire Red hack given the correct offsets (not tested)
- An interface using modals to for developers to access and modify configuration data through Discord
- An interface for developers to update the patch used by the bot at runtime through either Discord attachments or Mega
  links to a zip archive
- Exception traceback when using developer-only commands (that does not leak user information) for when something
  inevitably goes wrong

## Origin

One day, I got sick of seeing people ask "Hey, what are xxx's stats?" and "Hey what are xxx's levelup moves?" So, I
contacted Blushell, the main developer of the Touhoumon Revised hacks if I could make a bot for the server. And then
here we are like a month or something later with a bot that actually works (besides that the bot cannot upload sprites
yet) doesn't work.

But why did I choose the name Akyuu? Even if you're a devoted Touhou fan you might not even know she exists. Even I, as
someone who knows a thing or two about Touhou lore, almost forgot that she existed. Hieda no Akyuu is a human that
appears in the books "Perfect Memento in Strict Sense" and "Memorizable Gensokyo" as a main character. She is a
chronicler with the ability to remember everything she sees. Hieda no Akyuu is the current "Child of Miare" (御阿礼の子).
Every "Child of Miare" of the Hieda family is a reincarnation of the previous "Child of Miare", who inherits the
memories of the previous incarnates. She remembers everything, so you don't have to, just like this bot!

## Commands
### Slash Commands
Oftentimes, the command's description will be enough to know what it does
- `/help`
  - brings you here so you can read the documentation
- `/ping`
  - Check if the bot is online and get the bot's latency with Discord
- 
### Context Commands
#### Get Boneka Data
- Message command (right-click on a message and go to `Apps` on the dropdown on desktop)
- Looks at all the boneka names that are in the message and allows the user to find data on any of the Boneka
- 