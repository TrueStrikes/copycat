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
                send_reply(channel_id, replaced_content)
            else:
                print("Message:")
                print(content)
                send_reply(channel_id, content)

            user_messages.add(content)

def retrieve_latest_messages(channelid):
    headers = {
        'authorization': bot_token
    }
    params = {
        'limit': 2
    }
    r = requests.get(f'https://discord.com/api/v8/channels/{channelid}/messages', headers=headers, params=params)
    messages = json.loads(r.text)
    
    if not isinstance(messages, list) or len(messages) == 0:
        return []

    return messages

def send_reply(channelid, content):
    headers = {
        'authorization': bot_token
    }
    data = {
        'content': content  # Send the user's message content directly as the reply
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
    config = json.load(config_file)

bot_token = config["bot_token"]
channel_id = config["channel_id"]
target_user_ids = config["target_user_ids"]  # Use a list to store multiple targets
owner_id = config["ownerid"]
blacklist.update(word.lower() for word in config["blacklist"])

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
            config = json.load(config_file)

        bot_token = config["bot_token"]
        channel_id = config["channel_id"]
        target_user_ids = config["target_user_ids"]  # Update target_user_ids
        owner_id = config["ownerid"]
        blacklist.update(word.lower() for word in config["blacklist"])

        headers = {
            'authorization': bot_token
        }

        latest_messages = retrieve_latest_messages(channel_id)
        if latest_messages:
            for message in latest_messages:
                display_message(message)

    time.sleep(0.2)  # Add a wait time of 0.2 seconds before the next iteration
