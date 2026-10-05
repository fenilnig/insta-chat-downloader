import json
import os
from instagrapi import Client

SESSION_FILE = "dist/session.json"
CACHE_FILE = "message_cache.json"

cl = Client()
cl.load_settings(SESSION_FILE)
cl.get_timeline_feed()

threads = cl.direct_threads(amount=30)
target_thread = None
for thread in threads:
    if "legend_editx" in (thread.thread_title or "").lower() or any("legend_editx" in u.username.lower() for u in thread.users):
        target_thread = thread
        break

if target_thread:
    print(f"Fetching messages for {target_thread.id}...")
    messages = cl.direct_messages(target_thread.id, amount=100) # Just get 100 for debugging
    
    # Dump the raw dicts of the messages
    raw_msgs = [msg.model_dump() for msg in messages]
    
    with open(CACHE_FILE, "w") as f:
        json.dump(raw_msgs, f, indent=2, default=str)
        
    print(f"Dumped {len(messages)} messages to {CACHE_FILE}")
    
    # Also print some item_types we found
    types = set(msg.item_type for msg in messages)
    print("Found item types:", types)
    
    # Find any msg with 'clip', 'media_share', 'xma_story_share' etc
    for m in raw_msgs:
        if m.get('item_type') != 'text':
            print("Found non-text item:", m.get('item_type'))
