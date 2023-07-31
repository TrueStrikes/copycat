import requests
import json
import os
import time
import threading
import re

# Set to keep track of retrieved message IDs and user messages
retrieved_message_ids = set()
user_messages = set()
blacklist = set()
original_senders = {}

# Variable to indicate if the script is running
running = True

def display_message(message):
    message_id = message.get('id')
    if message_id not in retrieved_message_ids:
        retrieved_message_ids.add(message_id)
        author_id = message.get('author', {}).get('id')
        content = message.get('content')
        if author_id in target_user_ids and content not in user_messages:
            # Check if the message contains any blacklisted words as whole words
            pattern = r"\b(" + "|".join(map(re.escape, blacklist)) + r")\b"
            replaced_content = re.sub(pattern, "####", content, flags=re.IGNORECASE)
            if replaced_content != content:
                print("Replaced content:")
                print(replaced_content)
                reply_to_original_sender(channel_id, replaced_content, message_id)
            else:
                print("Message:")
                print(content)
                reply_to_original_sender(channel_id, content, message_id)

            user_messages.add(content)

def retrieve_latest_messages(channelid):
    headers = {
        'authorization': bot_token
    }
    params = {
        'limit': 2
    }
    r = requests.get(f'https://discord.com/api/v8/channels/{channelid}/messages', headers=headers, params=params)
    try:
        messages = json.loads(r.text)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        return []

    if not isinstance(messages, list) or len(messages) == 0:
        return []

    return messages

def reply_to_original_sender(channelid, content, message_id):
    headers = {
        'authorization': bot_token
    }
    data = {
        'content': content
    }

    # If the message_id exists in original_senders dictionary, reply to the original sender
    original_sender_id = original_senders.get(message_id)
    if original_sender_id:
        data['message_reference'] = {
            'message_id': message_id,
            'guild_id': None,
            'channel_id': channel_id
        }

    requests.post(f'https://discord.com/api/v8/channels/{channelid}/messages', headers=headers, json=data)

def input_thread():
    global running
    while True:
        if not running:
            user_input = input()
            if user_input.lower() == 'ctrl+z':
                running = True
                print("Script resumed.")
            else:
                print("Invalid input. Type 'ctrl+z' to resume script.")
        time.sleep(1)

# Read the configurations from config.json
with open('config.json', 'r') as config_file:
    try:
        config = json.load(config_file)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        config = {}  # If there's an error, initialize an empty config dictionary

bot_token = config.get("bot_token", "")
channel_id = config.get("channel_id", "")
target_user_ids = config.get("target_user_ids", [])  # Use a list to store multiple targets
owner_id = config.get("ownerid", "")
blacklist.update(word.lower() for word in config.get("blacklist", []))

# Clear the console and print "The bot is working, showing messages in the channel."
print("The bot is working, showing messages in the channel.")

# Start a separate thread to listen for user input
input_thread = threading.Thread(target=input_thread)
input_thread.daemon = True
input_thread.start()

# Set the loop to run indefinitely
while True:
    if running:
        with open('config.json', 'r') as config_file:
            try:
                config = json.load(config_file)
            except json.JSONDecodeError as e:
                print("JSON decode error:", e)
                config = {}  # If there's an error, initialize an empty config dictionary

        bot_token = config.get("bot_token", "")
        channel_id = config.get("channel_id", "")
        target_user_ids = config.get("target_user_ids", [])  # Update target_user_ids
        owner_id = config.get("ownerid", "")
        blacklist.update(word.lower() for word in config.get("blacklist", []))

        headers = {
            'authorization': bot_token
        }

        latest_messages = retrieve_latest_messages(channel_id)
        if latest_messages:
            for message in latest_messages:
                display_message(message)

    time.sleep(0.2)  # Add a wait time of 0.2 seconds before the next iteration
