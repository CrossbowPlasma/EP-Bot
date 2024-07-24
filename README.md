# Earning Potential Discord Bot

Welcome to the Earning Potential Discord Bot! This bot enhances the user experience in the Earning Potential online community by providing points-based rewards, tracking user activities, and offering detailed logging features.

## Features

### Commands

- **!addpoints (Moderator only)**
  - Adds points to a user.
  - **Usage:** `!addpoints @user <points>`

- **!removepoints (Moderator only)**
  - Removes points from a user.
  - **Usage:** `!removepoints @user <points>`

- **!points**
  - Displays the current points of the user or another user if mentioned.
  - **Usage:** `!points [@user]`

- **!leaderboard**
  - Displays the leaderboard of users with the highest points.
  - **Usage:** `!leaderboard`

- **!logsetup (Moderator only)**
  - Sets up logging channels for various activities.
  - **Usage:** `!logsetup`

### Logging

- **Voice Channel Activities**
  - Logs when users join, leave, or transfer between voice channels.
  - Maintains links to previous join/transfer logs for end-to-end tracking.
  - Tracks the time spent in voice channels, including cumulative time if transfers are involved.
  - Pings a specified role to join the voice channel after a user has been in the voice channel for a certain amount of time.

- **Command Usage**
  - Logs who used what command, except for the `!logsetup` command.

- **Bad Language Detection**
  - Detects the use of bad words, logs the incident, deletes the offending message, and removes points from the user who used the bad word.

- **Daily Interaction Rewards**
  - Awards points to users for daily interactions to encourage active participation.

- **Points on Reaction**
  - Awards points when a moderator reacts to a user's message with the ✅ emote.
  - Logs the reaction event, including which user received the points and the number of points awarded.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `discord.py` library
