import discord
from discord.ext import commands, tasks
from discord.ext.commands import MissingAnyRole
from datetime import datetime, timedelta

# Bot configuration
# Set up the bot's intents to listen to various events
intents = discord.Intents.default()
intents.messages = True          # Listen to messages
intents.message_content = True   # Access message content
intents.reactions = True         # Listen to reactions
intents.voice_states = True      # Track voice state changes

# Create bot instance with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot token (keep this confidential)
BOT_TOKEN = ""

# Default channel IDs for logging
PRIMARY_LOG_CHANNEL_ID =   # Main channel for general logs
POINTS_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for logging points (Not in use)
REACT_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for reaction logs
FOUL_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for foul language logs
LEADERBOARD_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for leaderboard updates
VC_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for voice chat logs
ENCOURAGEMENT_LOG_CHANNEL_ID = PRIMARY_LOG_CHANNEL_ID  # Channel for encouragement logs
ENCOURAGEMENT_SEND_CHANNEL_ID =   # Channel for sending encouragement messages


# List of moderator role IDs (for command access)
MODERATOR_ROLE_IDS = []

# Voice channel monitoring settings
user_vc_entry_time = {}  # Tracks when users join voice channels
user_vc_logs = {}        # Logs related to voice channel activities
CHECK_INTERVAL_MINUTES =   # Interval for checking voice channel activities
ENCOURAGEMENT_ROLE_ID =   # Role to ping for encouragement messages

# In-memory storage for bot data
user_points = {}          # Points for users
user_message_counts = {} # Daily message counts for users
foul_language_words = []  # Words to detect and handle










# Define your bot commands, events, and tasks here

# ---------------------------------
# Helper Functions
# ---------------------------------

# Helper Function: Get a log channel by its ID
async def get_log_channel(channel_id):
    """
    Retrieves a Discord channel object using its ID.

    Fetches the channel from the bot's cache using its unique ID.

    Parameters:
    - channel_id (int): The ID of the channel to retrieve.

    Returns:
    - discord.TextChannel: The channel object if found; otherwise, None.
    """
    return bot.get_channel(channel_id)


# Helper Function: Create an embed for logging with dynamic colors
async def create_log_embed(title, description, fields=[], color=discord.Color.default()):
    """
    Constructs a Discord embed message with dynamic properties for logging.

    Creates an embed with a title, description, optional fields, and color.
    Includes a timestamp footer for when the log was created.

    Parameters:
    - title (str): The title of the embed.
    - description (str): The description text for the embed.
    - fields (list of tuples): Optional. List of tuples with field names and values.
    - color (discord.Color): Optional. Color of the embed. Defaults to default color.

    Returns:
    - discord.Embed: The created embed object.
    """
    embed = discord.Embed(
        title=title,                # Title of the embed
        description=description,    # Description text
        color=color                 # Color of the embed
    )
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)  # Add fields to the embed
    embed.set_footer(text=f"Logged at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")  # Timestamp footer
    return embed


# Helper Function: Send a log message to the appropriate channel
async def log_action(log_type, title, description, fields=[]):
    """
    Sends a log message to the designated channel based on the log type.

    Maps log types to channels and colors, creates an embed with title, description, and fields,
    and sends it to the appropriate channel. Returns the message ID if successful.

    Parameters:
    - log_type (str): The type of log (e.g., 'points', 'reaction', 'foul_language').
    - title (str): The title of the log message.
    - description (str): The description or details of the log message.
    - fields (list of tuples): Optional. List of tuples with field names and values for the embed.

    Returns:
    - int: The message ID of the sent log message if successful; otherwise, None.
    """
    # Map log types to channel IDs
    channel_mapping = {
        "points": POINTS_LOG_CHANNEL_ID,
        "reaction": REACT_LOG_CHANNEL_ID,
        "foul_language": FOUL_LOG_CHANNEL_ID,
        "leaderboard": LEADERBOARD_LOG_CHANNEL_ID,
        "vc": VC_LOG_CHANNEL_ID,
        "encouragement": ENCOURAGEMENT_LOG_CHANNEL_ID,
        "default": PRIMARY_LOG_CHANNEL_ID
    }

    # Map log types to colors
    color_mapping = {
        "add_points": discord.Color.green(),    # Color for adding points logs
        "remove_points": discord.Color.red(),   # Color for removing points logs
        "reaction": discord.Color.fuchsia(),    # Color for reaction logs
        "foul_language": discord.Color.red(),   # Color for foul language logs
        "leaderboard": discord.Color.gold(),    # Color for leaderboard logs
        "vc_join": discord.Color.green(),       # Color for voice channel join logs
        "vc_leave": discord.Color.red(),        # Color for voice channel leave logs
        "vc_switch": discord.Color.yellow(),    # Color for voice channel switch logs
        "encouragement": discord.Color.purple(),# Color for encouragement logs
        "default": discord.Color.default()      # Default color
    }

    # Get the log channel ID based on log type, default to primary log channel
    log_channel_id = channel_mapping.get(log_type, PRIMARY_LOG_CHANNEL_ID)
    log_channel = await get_log_channel(log_channel_id)  # Fetch the log channel based on ID
    color = color_mapping.get(log_type, discord.Color.blue())  # Get the color based on log type, default to blue

    if log_channel:
        # Create the embed with the given title, description, fields, and color
        embed = await create_log_embed(title, description, fields, color)
        # Send the embed message to the log channel
        message = await log_channel.send(embed=embed)
        return message.id  # Return the message ID of the sent log message
    else:
        print(f"Log channel with ID {log_channel_id} not found.")  # Log error if the channel is not found
        return None


# Helper Function: Create a user points embed
def create_user_points_embed(user, points, reason):
    """
    Generates an embed to show changes in user points.

    Creates an embed showing points gained or lost, with reason and updated total points.
    Uses green for gains and red for losses.

    Parameters:
    - user (discord.User): The user whose points have changed.
    - points (int): Number of points gained (positive) or lost (negative).
    - reason (str): The reason for the points change.

    Returns:
    - discord.Embed: The created embed object showing the points change.
    """
    embed = discord.Embed(
        title="Points Updated",                                      # Title of the embed
        description=f"{user.mention} has {'gained' if points > 0 else 'lost'} {abs(points)} points for {reason}.",  # Description
        color=discord.Color.green() if points > 0 else discord.Color.red()  # Color based on points change
    )
    embed.add_field(name="Total Points", value=f"{user_points[user.id]}", inline=False)  # Show total points
    return embed










# ---------------------------------
# Events
# ---------------------------------

# Event: Bot startup
@bot.event
async def on_ready():
    """
    Triggered when the bot is ready and connected to Discord.

    Actions:
    - Starts background tasks for resetting daily messages and checking VC encouragement.
    - Logs the bot startup event.
    """
    # Start the background tasks
    reset_daily_messages.start()
    check_vc_encouragement.start()

    # Log the bot startup event
    await log_action(
        log_type="default",
        title="Bot Started",
        description="The bot has started running."
    )

    print(f'Bot is ready. Logged in as {bot.user}')


# Event: Message received
@bot.event
async def on_message(message):
    """
    Triggered when a new message is received in any channel.

    Actions:
    - Tracks and increments message count for users.
    - Awards points for sending 10 messages in a day.
    - Detects and handles foul language, deducting points and deleting messages if necessary.
    """
    # Ignore messages from bots
    if message.author.bot:
        return

    user_id = message.author.id
    today = datetime.utcnow().date()

    # Initialize or reset the user's message count for today
    if user_id not in user_message_counts:
        user_message_counts[user_id] = {'date': today, 'count': 0}

    if user_message_counts[user_id]['date'] != today:
        user_message_counts[user_id] = {'date': today, 'count': 0}

    # Increment the user's message count
    user_message_counts[user_id]['count'] += 1

    # Award points if the user has sent 10 messages today
    if user_message_counts[user_id]['count'] == 10:
        if user_id not in user_points:
            user_points[user_id] = 0
        user_points[user_id] += 0.5
        await message.channel.send(embed=create_user_points_embed(message.author, 0.5, "sending 10 messages today"))
        await log_action(
            log_type="points",
            title="Points Awarded",
            description="Points awarded for sending 10 messages today.",
            fields=[
                ("Performed by", f"{message.author.mention}"),
                ("Action", "0.5 points awarded"),
            ]
        )

    # Detect and handle foul language
    if any(foul_word in message.content.lower() for foul_word in foul_language_words):
        if user_id not in user_points:
            user_points[user_id] = 0
        user_points[user_id] -= 10
        await message.delete()  # Delete the message with foul language
        await message.channel.send(embed=create_user_points_embed(message.author, -10, "using foul language"))
        await log_action(
            log_type="foul_language",
            title="Foul Language Detected",
            description="Foul language detected and points deducted.",
            fields=[
                ("User", f"{message.author.mention}"),
                ("Bad Word", f"{', '.join(foul_word for foul_word in foul_language_words if foul_word in message.content.lower())}"),
                ("Action", "10 points deducted and message deleted"),
                ("Message Link", f"[Jump to message]({message.jump_url})"),
            ]
        )

    # Process any other commands in the message
    await bot.process_commands(message)


# Event: Reaction added
@bot.event
async def on_reaction_add(reaction, user):
    """
    Triggered when a reaction is added to a message.

    Actions:
    - Checks if the reaction is a tick emoji and from a moderator.
    - Awards 2 points to the message author for a tick reaction from a moderator.
    """
    # Ignore reactions from bots or non-tick emojis
    if user.bot or reaction.emoji != '✅':
        return

    # Check if the user has a moderator role
    if any(role.id in MODERATOR_ROLE_IDS for role in user.roles):
        message_author = reaction.message.author

        # Award 2 points to the message author
        if message_author.id not in user_points:
            user_points[message_author.id] = 0
        user_points[message_author.id] += 2

        await reaction.message.channel.send(embed=create_user_points_embed(
            message_author, 2, "receiving a tick reaction from a moderator"))
        await log_action(
            log_type="reaction",
            title="Points Awarded via Reaction",
            description="Points awarded for a reaction on a message.",
            fields=[
                ("Message", f"{reaction.message.content}"),
                ("Moderator", f"{user.mention}"),
                ("Author", f"{message_author.mention}"),
                ("Action", "2 points awarded"),
                ("Message Link", f"[Jump to message]({reaction.message.jump_url})"),
            ]
        )


# Event: Voice state update
@bot.event
async def on_voice_state_update(member, before, after):
    """
    Triggered when a user changes their voice state (joins, switches, or leaves a voice channel).

    Actions:
    - Logs voice channel joins and stores entry times.
    - Logs voice channel switches and calculates time spent in each channel.
    - Logs voice channel leaves, calculates total time spent, and clears stored logs.
    """
    # Handle voice channel join
    if before.channel is None and after.channel is not None:
        user_vc_entry_time[member.id] = {'entry_time': datetime.utcnow(), 'vc_channel_id': after.channel.id}
        log_message_id = await log_action(
            log_type="vc_join",
            title="Voice Channel Join",
            description=f"{member.mention} joined the voice channel {after.channel.mention}.",
            fields=[
                ("User", f"{member.mention}"),
                ("Channel", f"{after.channel.mention}"),
                ("Action", "Joined voice channel")
            ]
        )
        if log_message_id:
            user_vc_logs[member.id] = {'join': log_message_id, 'total_time': 0}  # Store join log message ID and initialize total time

    # Handle voice channel switch
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        entry_data = user_vc_entry_time.get(member.id, {})
        entry_time = entry_data.get('entry_time')
        if entry_time:
            # Calculate time spent in the previous voice channel
            time_spent = datetime.utcnow() - entry_time
            time_spent_seconds = int(time_spent.total_seconds())
            time_spent_str = str(timedelta(seconds=time_spent_seconds))

            # Update entry time for the new channel
            user_vc_entry_time[member.id] = {'entry_time': datetime.utcnow(), 'vc_channel_id': after.channel.id}

            join_log_message_id = user_vc_logs.get(member.id, {}).get('join')
            transfer_log_message_id = user_vc_logs.get(member.id, {}).get('transfer')

            # Get the link to the previous log message if available
            message_link = None
            if transfer_log_message_id:
                transfer_log_message = await bot.get_channel(VC_LOG_CHANNEL_ID).fetch_message(transfer_log_message_id)
                message_link = f"[Jump to transfer log]({transfer_log_message.jump_url})"
            elif join_log_message_id:
                join_log_message = await bot.get_channel(VC_LOG_CHANNEL_ID).fetch_message(join_log_message_id)
                message_link = f"[Jump to join log]({join_log_message.jump_url})"

            # Log the voice channel switch
            switch_log_message_id = await log_action(
                log_type="vc_switch",
                title="Voice Channel Switch",
                description=f"{member.mention} switched from {before.channel.mention} to {after.channel.mention}.",
                fields=[
                    ("User", f"{member.mention}"),
                    ("From Channel", f"{before.channel.mention}"),
                    ("To Channel", f"{after.channel.mention}"),
                    ("Time Spent", f"{time_spent_str}"),
                    ("Log Link", message_link),
                ]
            )
            if switch_log_message_id:
                user_vc_logs[member.id]['transfer'] = switch_log_message_id  # Store transfer log message ID
                user_vc_logs[member.id]['total_time'] = user_vc_logs[member.id].get('total_time', 0) + time_spent_seconds

    # Handle voice channel leave
    elif before.channel is not None and after.channel is None:
        entry_data = user_vc_entry_time.get(member.id, {})
        entry_time = entry_data.get('entry_time')
        if entry_time:
            # Calculate time spent in the voice channel before leaving
            time_spent = datetime.utcnow() - entry_time
            time_spent_seconds = int(time_spent.total_seconds())
            time_spent_str = str(timedelta(seconds=time_spent_seconds))

            transfer_log_message_id = user_vc_logs.get(member.id, {}).get('transfer')
            join_log_message_id = user_vc_logs.get(member.id, {}).get('join')

            # Get the link to the previous log message if available
            message_link = None
            if transfer_log_message_id:
                transfer_log_message = await bot.get_channel(VC_LOG_CHANNEL_ID).fetch_message(transfer_log_message_id)
                message_link = f"[Jump to transfer log]({transfer_log_message.jump_url})"
            elif join_log_message_id:
                join_log_message = await bot.get_channel(VC_LOG_CHANNEL_ID).fetch_message(join_log_message_id)
                message_link = f"[Jump to join log]({join_log_message.jump_url})"

            # Calculate total time spent in voice channels
            total_time_seconds = user_vc_logs.get(member.id, {}).get('total_time', 0) + time_spent_seconds
            total_time_str = str(timedelta(seconds=total_time_seconds)) if total_time_seconds > 0 else "N/A"

            # Log the voice channel leave
            await log_action(
                log_type="vc_leave",
                title="Voice Channel Leave",
                description=f"{member.mention} left the voice channel {before.channel.mention}.",
                fields=[
                    ("User", f"{member.mention}"),
                    ("Channel", f"{before.channel.mention}"),
                    ("Time Spent", f"{time_spent_str}"),
                    ("Total Time Spent", f"{total_time_str}"),
                    ("Log Link", message_link),
                ]
            )
            # Clear the user's voice channel logs
            if member.id in user_vc_logs:
                del user_vc_logs[member.id]
            if member.id in user_vc_entry_time:
                del user_vc_entry_time[member.id]


# Event: Interaction
@bot.event
async def on_interaction(interaction: discord.Interaction):
    """
    Handles interactions with the bot, such as dropdown menu selections and button clicks.

    Parameters:
    - interaction: The interaction object containing information about the interaction.

    Actions:
    - Processes the dropdown menu for selecting the log type.
    - Processes the dropdown menu for selecting the channel.
    - Processes the dropdown menu for changing the log type.
    - Handles the "Done" button click to finalize the setup.
    """
    # Create "Done" button with green color
    done_button = discord.ui.Button(
        label="Done",
        style=discord.ButtonStyle.success, 
        custom_id="done_button"
    )

    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        values = interaction.data.get("values", [])

        # Handle the dropdown menu for selecting the log type
        if custom_id == "select_log_type":
            selected_log_type = values[0]

            # Create dropdown menu for channel selection
            options = [discord.SelectOption(label="None", value="None")]
            for channel in interaction.guild.channels:
                if isinstance(channel, discord.TextChannel):  # Only include text channels
                    options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))

            select_channel = discord.ui.Select(
                placeholder=f"Select a channel for {selected_log_type}...", 
                options=options, 
                custom_id=f"select_{selected_log_type}"
            )

            # Re-create dropdown menu for changing log type
            log_type_options = [
                discord.SelectOption(label="Primary Log Channel", value="primary_log_channel"),
                discord.SelectOption(label="Points Log Channel", value="points_log_channel"),
                discord.SelectOption(label="Reaction Log Channel", value="reaction_log_channel"),
                discord.SelectOption(label="Foul Language Log Channel", value="foul_log_channel"),
                discord.SelectOption(label="Leaderboard Log Channel", value="leaderboard_log_channel"),
                discord.SelectOption(label="Voice Log Channel", value="voice_log_channel"),
                discord.SelectOption(label="Encouragement Log Channel", value="encouragement_log_channel")
            ]

            select_log_type = discord.ui.Select(
                placeholder="Change log type...", 
                options=log_type_options, 
                custom_id="change_log_type"
            )

            # Create a view to hold both select menus and the "Done" button
            view = discord.ui.View()
            view.add_item(select_channel)
            view.add_item(select_log_type)
            view.add_item(done_button)

            # Edit the original message with the updated view
            await interaction.response.edit_message(
                content=f"Select a channel for the {selected_log_type} log channel or change the log type:", 
                view=view
            )

        # Handle the dropdown menu for selecting the channel
        elif custom_id.startswith("select_"):
            log_type = custom_id[len("select_"):]
            selected_channel_id = values[0]

            if selected_channel_id == "None":
                await interaction.response.send_message(f"No channel selected for {log_type}.", ephemeral=True)
                return

            # Update the appropriate log channel variable
            global_vars = {
                "primary_log_channel": "PRIMARY_LOG_CHANNEL_ID",
                "points_log_channel": "POINTS_LOG_CHANNEL_ID",
                "reaction_log_channel": "REACT_LOG_CHANNEL_ID",
                "foul_log_channel": "FOUL_LOG_CHANNEL_ID",
                "leaderboard_log_channel": "LEADERBOARD_LOG_CHANNEL_ID",
                "voice_log_channel": "VC_LOG_CHANNEL_ID",
                "encouragement_log_channel": "ENCOURAGEMENT_LOG_CHANNEL_ID"
            }
            log_channel_var = global_vars.get(log_type)
            if log_channel_var:
                globals()[log_channel_var] = int(selected_channel_id)

            # Update the log setup embed
            embed = discord.Embed(title="Current Log Setup", color=discord.Color.default())
            embed.add_field(name="Primary Log Channel", value=f"<#{PRIMARY_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Points Log Channel", value=f"<#{POINTS_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Reaction Log Channel", value=f"<#{REACT_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Foul Language Log Channel", value=f"<#{FOUL_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Leaderboard Log Channel", value=f"<#{LEADERBOARD_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Voice Channel Log Channel", value=f"<#{VC_LOG_CHANNEL_ID}>", inline=False)
            embed.add_field(name="Encouragement Log Channel", value=f"<#{ENCOURAGEMENT_LOG_CHANNEL_ID}>", inline=False)

            # Re-create dropdown menus and "Done" button
            log_type_options = [
                discord.SelectOption(label="Primary Log Channel", value="primary_log_channel"),
                discord.SelectOption(label="Points Log Channel", value="points_log_channel"),
                discord.SelectOption(label="Reaction Log Channel", value="reaction_log_channel"),
                discord.SelectOption(label="Foul Language Log Channel", value="foul_log_channel"),
                discord.SelectOption(label="Leaderboard Log Channel", value="leaderboard_log_channel"),
                discord.SelectOption(label="Voice Log Channel", value="voice_log_channel"),
                discord.SelectOption(label="Encouragement Log Channel", value="encouragement_log_channel")
            ]

            select_log_type = discord.ui.Select(
                placeholder="Change log type...", 
                options=log_type_options, 
                custom_id="change_log_type"
            )

            options = [discord.SelectOption(label="None", value="None")]
            for channel in interaction.guild.channels:
                if isinstance(channel, discord.TextChannel):  # Only include text channels
                    options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))

            select_channel = discord.ui.Select(
                placeholder=f"Select a channel...", 
                options=options, 
                custom_id=f"select_{log_type}"
            )

            view = discord.ui.View()
            view.add_item(select_channel)
            view.add_item(select_log_type)
            view.add_item(done_button)

            # Edit the original message with the updated embed and view
            await interaction.response.edit_message(embed=embed, view=view)

        # Handle the dropdown menu for changing the log type
        elif custom_id == "change_log_type":
            selected_log_type = values[0]

            # Create dropdown menu for channel selection
            options = [discord.SelectOption(label="None", value="None")]
            for channel in interaction.guild.channels:
                if isinstance(channel, discord.TextChannel):  # Only include text channels
                    options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))

            select_channel = discord.ui.Select(
                placeholder=f"Select a channel for {selected_log_type}...", 
                options=options, 
                custom_id=f"select_{selected_log_type}"
            )

            # Re-create dropdown menus and "Done" button
            log_type_options = [
                discord.SelectOption(label="Primary Log Channel", value="primary_log_channel"),
                discord.SelectOption(label="Points Log Channel", value="points_log_channel"),
                discord.SelectOption(label="Reaction Log Channel", value="reaction_log_channel"),
                discord.SelectOption(label="Foul Language Log Channel", value="foul_log_channel"),
                discord.SelectOption(label="Leaderboard Log Channel", value="leaderboard_log_channel"),
                discord.SelectOption(label="Voice Log Channel", value="voice_log_channel"),
                discord.SelectOption(label="Encouragement Log Channel", value="encouragement_log_channel")
            ]

            select_log_type = discord.ui.Select(
                placeholder="Change log type...", 
                options=log_type_options, 
                custom_id="change_log_type"
            )

            view = discord.ui.View()
            view.add_item(select_channel)
            view.add_item(select_log_type)
            view.add_item(done_button)

            # Edit the original message with the updated view
            await interaction.response.edit_message(
                content=f"Select a channel for the {selected_log_type} log channel or change the log type:", 
                view=view
            )

        # Handle the "Done" button
        elif custom_id == "done_button":
            # Send a completion message
            await interaction.response.send_message("Log setup process is now complete.", ephemeral=True)

            # Edit the original message to remove all components (buttons and dropdowns)
            await interaction.message.edit(
                content="Log setup process is now complete.",
                view=None  # Remove all components
            )










# ---------------------------------
# Commands
# ---------------------------------

# Command: Add Points
@bot.command(name='addpoints')
@commands.has_any_role(*MODERATOR_ROLE_IDS)
async def add_points(ctx, member: discord.Member, points: float):
    """
    Adds points to a specified member.

    Parameters:
    - ctx: Context of the command invocation.
    - member: The member to whom points will be added.
    - points: The number of points to add.

    Actions:
    - Adds the specified points to the member's total points.
    - Sends a confirmation message with the updated points.
    - Logs the action with details of the command usage.
    """
    try:
        if member.id not in user_points:
            user_points[member.id] = 0
        user_points[member.id] += points
        await ctx.send(embed=create_user_points_embed(member, points, "added by command"))
        await log_action(
            log_type="add_points",
            title="Add Points Command",
            description="Points added to a member.",
            fields=[
                ("Command used by", f"{ctx.author.mention}"),
                ("Member affected", f"{member.mention}"),
                ("Action", f"Added {points} points"),
            ]
        )
    except MissingAnyRole:
        await ctx.send("You do not have the required role to use this command.")
        print(f"Error: {ctx.author} tried to use 'addpoints' without required roles.")


# Command: Remove Points
@bot.command(name='removepoints')
@commands.has_any_role(*MODERATOR_ROLE_IDS)
async def remove_points(ctx, member: discord.Member, points: float):
    """
    Removes points from a specified member.

    Parameters:
    - ctx: Context of the command invocation.
    - member: The member from whom points will be removed.
    - points: The number of points to remove.

    Actions:
    - Deducts the specified points from the member's total points.
    - Sends a confirmation message with the updated points.
    - Logs the action with details of the command usage.
    """
    try:
        if member.id not in user_points:
            user_points[member.id] = 0
        user_points[member.id] -= points
        await ctx.send(embed=create_user_points_embed(member, -points, "removed by command"))
        await log_action(
            log_type="remove_points",
            title="Remove Points Command",
            description="Points removed from a member.",
            fields=[
                ("Command used by", f"{ctx.author.mention}"),
                ("Member affected", f"{member.mention}"),
                ("Action", f"Removed {points} points"),
            ]
        )
    except MissingAnyRole:
        await ctx.send("You do not have the required role to use this command.")
        print(f"Error: {ctx.author} tried to use 'removepoints' without required roles.")
    except Exception as e:
        await ctx.send("An error occurred while processing the command.")
        print(f"Error: {e}")


# Command: Check Points
@bot.command(name='points')
async def check_points(ctx, member: discord.Member = None):
    """
    Checks and displays the points of a specified member or the command user.

    Parameters:
    - ctx: Context of the command invocation.
    - member: The member whose points will be checked. Defaults to the command user if not specified.

    Actions:
    - Retrieves the points for the specified member.
    - Sends an embed message displaying the member's points.
    - Logs the action with details of the command usage and the points checked.
    """
    member = member or ctx.author
    points = user_points.get(member.id, 0)
    embed = discord.Embed(
        title="Points Check",
        description=f"{member.mention} has {points} points.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    await log_action(
        log_type="default",
        title="Points Command",
        description="Points checked for a member.",
        fields=[
            ("Command used by", f"{ctx.author.mention}"),
            ("Member checked", f"{member.mention}"),
            ("Points", f"{points}"),
            ("Message Link", f"[Jump to message]({ctx.message.jump_url})")
        ]
    )


# Command: Leaderboard
@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """
    Displays the leaderboard showing the top 10 members with the highest points.

    Parameters:
    - ctx: Context of the command invocation.

    Actions:
    - Retrieves and sorts members based on their points.
    - Constructs an embed message listing the top 10 members and their points.
    - Sends the leaderboard embed message.
    - Logs the action with details of the command usage.
    """
    sorted_users = sorted(user_points.items(), key=lambda item: item[1], reverse=True)
    if not sorted_users:
        await ctx.send("No points data available.")
        return

    embed = discord.Embed(title="Leaderboard", color=discord.Color.gold())

    # Adding top 10 users to the embed
    for i, (user_id, points) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(user_id)
        embed.add_field(name=f"{i}. {user.name}", value=f"{points} points", inline=False)

    await ctx.send(embed=embed)
    await log_action(
        log_type="leaderboard",
        title="Leaderboard Command",
        description="Leaderboard displayed.",
        fields=[
            ("Command used by", f"{ctx.author.mention}"),
            ("Message Link", f"[Jump to message]({ctx.message.jump_url})"),
        ]
    )


# Command: Log Setup
@bot.command(name='logsetup')
@commands.has_any_role(*MODERATOR_ROLE_IDS)
async def logsetup(ctx):
    """
    Displays the current log setup of the server and allows setting up channels.

    Parameters:
    - ctx: Context of the command invocation.

    Actions:
    - Creates an embed displaying the current log channel configurations.
    - Adds a dropdown menu for selecting log types to configure.
    - Adds a "Done" button for finalizing the setup.
    - Sends the embed message with the interactive view attached.
    """
    embed = discord.Embed(title="Current Log Setup", color=discord.Color.default())

    # Add log channel details to the embed
    embed.add_field(name="Primary Log Channel", value=f"<#{PRIMARY_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Points Log Channel", value=f"<#{POINTS_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Reaction Log Channel", value=f"<#{REACT_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Foul Language Log Channel", value=f"<#{FOUL_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Leaderboard Log Channel", value=f"<#{LEADERBOARD_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Voice Channel Log Channel", value=f"<#{VC_LOG_CHANNEL_ID}>", inline=False)
    embed.add_field(name="Encouragement Log Channel", value=f"<#{ENCOURAGEMENT_LOG_CHANNEL_ID}>", inline=False)

    # Define options for the log type dropdown menu
    log_type_options = [
        discord.SelectOption(label="Primary Log Channel", value="primary_log_channel"),
        discord.SelectOption(label="Points Log Channel", value="points_log_channel"),
        discord.SelectOption(label="Reaction Log Channel", value="reaction_log_channel"),
        discord.SelectOption(label="Foul Language Log Channel", value="foul_log_channel"),
        discord.SelectOption(label="Leaderboard Log Channel", value="leaderboard_log_channel"),
        discord.SelectOption(label="Voice Log Channel", value="voice_log_channel"),
        discord.SelectOption(label="Encouragement Log Channel", value="encouragement_log_channel")
    ]

    # Create dropdown menu for selecting log type
    select_log_type = discord.ui.Select(
        placeholder="Select a log type to configure...",
        options=log_type_options,
        custom_id="select_log_type"
    )

    # Create "Done" button with green color
    done_button = discord.ui.Button(
        label="Done",
        style=discord.ButtonStyle.success,
        custom_id="done_button"
    )

    # Create a view to hold the select menu and button
    view = discord.ui.View()
    view.add_item(select_log_type)
    view.add_item(done_button)

    # Send the initial message with the view attached
    message = await ctx.send(embed=embed, view=view)
    logsetup_message_id = message.id  # Store the message ID for reference if needed










# ---------------------------------
# Tasks
# ---------------------------------

# Task: Reset daily message counts
@tasks.loop(hours=24)
async def reset_daily_messages():
    """
    Periodically resets daily message counts for all users.

    Actions:
    - Resets the message count and date for each user to the current date.
    - Logs the daily reset event.
    """
    # Reset the count and date for each user
    for user_id in user_message_counts:
        user_message_counts[user_id] = {'date': datetime.utcnow().date(), 'count': 0}

    # Log the daily reset event
    await log_action(log_type="default", title="Daily Reset", description="Daily message counts reset.")


# Task: Send encouragement messages for voice channel participation
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_vc_encouragement():
    """
    Periodically checks users' voice channel entry times and sends encouragement messages.

    Actions:
    - Checks the time spent by users in voice channels.
    - Sends an encouragement message if the user has been in the voice channel for a specified duration.
    - Logs the encouragement message event.
    """
    # Check each user's voice channel entry time and send encouragement if needed
    for user_id, data in list(user_vc_entry_time.items()):
        entry_time = data['entry_time']
        vc_channel_id = data['vc_channel_id']
        current_time = datetime.utcnow()
        time_spent = current_time - entry_time

        # Send encouragement message if time spent exceeds the threshold
        if time_spent >= timedelta(minutes=CHECK_INTERVAL_MINUTES):
            vc_channel = bot.get_channel(vc_channel_id)
            if vc_channel:
                encouragement_role = discord.utils.get(vc_channel.guild.roles, id=ENCOURAGEMENT_ROLE_ID)
                if encouragement_role:
                    encouragement_channel = bot.get_channel(ENCOURAGEMENT_SEND_CHANNEL_ID)
                    if encouragement_channel:
                        encouragement_message = f"Hey {encouragement_role.mention}, join the voice channel {vc_channel.mention} for some fun!"
                        sent_message = await encouragement_channel.send(encouragement_message)

                        # Log the encouragement message event
                        await log_action(
                            log_type="encouragement",
                            title="Encouragement Message Sent",
                            description=f"Encouragement message sent to {encouragement_channel.mention}.",
                            fields=[
                                ("Voice Channel", f"{vc_channel.mention}"),
                                ("Role", f"{encouragement_role.mention}"),
                                ("Message Link", f"[Jump to message]({sent_message.jump_url})")
                            ]
                        )










# Run the bot
bot.run(BOT_TOKEN)
