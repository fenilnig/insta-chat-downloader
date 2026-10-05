import os
import sys
import traceback
import re
import time
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
from instagrapi.mixins.challenge import ChallengeChoice
from colorama import init, Fore, Style, Back

# Initialize colorama for Windows
init()

SESSION_FILE = "session.json"
CONFIG_FILE = "config.json"
HISTORY_FILE = "download_history.json"

# ─── UI Helpers ───────────────────────────────────────────────

def banner():
    print(f"""{Fore.MAGENTA}{Style.BRIGHT}
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║   ██╗███╗   ██╗███████╗████████╗ █████╗              ║
    ║   ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗             ║
    ║   ██║██╔██╗ ██║███████╗   ██║   ███████║             ║
    ║   ██║██║╚██╗██║╚════██║   ██║   ██╔══██║             ║
    ║   ██║██║ ╚████║███████║   ██║   ██║  ██║             ║
    ║   ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝             ║
    ║                                                      ║
    ║     {Fore.WHITE}Chat Media Downloader{Fore.MAGENTA}    v2.0              ║
    ║     {Fore.CYAN}Reels • Posts • Stories • Links{Fore.MAGENTA}             ║
    ║                                                      ║
    ║     {Fore.YELLOW}Made by Legend Editx{Fore.MAGENTA}                         ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)

def print_header(text):
    width = 52
    print(f"\n{Fore.CYAN}{Style.BRIGHT}  ┌{'─' * width}┐")
    print(f"  │{text.center(width)}│")
    print(f"  └{'─' * width}┘{Style.RESET_ALL}")

def print_success(text):
    print(f"  {Fore.GREEN}{Style.BRIGHT}✓{Style.RESET_ALL} {Fore.GREEN}{text}{Style.RESET_ALL}")

def print_error(text):
    print(f"  {Fore.RED}{Style.BRIGHT}✗{Style.RESET_ALL} {Fore.RED}{text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"  {Fore.YELLOW}{Style.BRIGHT}⚠{Style.RESET_ALL} {Fore.YELLOW}{text}{Style.RESET_ALL}")

def print_info(text):
    print(f"  {Fore.CYAN}ℹ{Style.RESET_ALL} {text}")

def print_step(text):
    print(f"  {Fore.MAGENTA}{Style.BRIGHT}▸{Style.RESET_ALL} {text}")

def prompt(text):
    return input(f"  {Fore.YELLOW}{Style.BRIGHT}▸{Style.RESET_ALL} {text}")

def print_progress(current, total, media_id=""):
    bar_len = 30
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = f"{Fore.MAGENTA}{'█' * filled}{Fore.WHITE}{'░' * (bar_len - filled)}{Style.RESET_ALL}"
    pct = int(100 * current / total) if total > 0 else 0
    print(f"\r  {bar} {Fore.CYAN}{pct}%{Style.RESET_ALL} ({current}/{total}) {Fore.WHITE}{media_id[:30]}{Style.RESET_ALL}    ", end="", flush=True)

def print_summary_box(title, items):
    width = 52
    print(f"\n{Fore.GREEN}{Style.BRIGHT}  ╔{'═' * width}╗")
    print(f"  ║{title.center(width)}║")
    print(f"  ╠{'═' * width}╣")
    for item in items:
        padded = f"  {item}".ljust(width)
        print(f"  ║{padded}║")
    print(f"  ╚{'═' * width}╝{Style.RESET_ALL}")

# ─── Config ───────────────────────────────────────────────────

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(list(history), f)

# Load global history
downloaded_history = load_history()

# ─── Login ────────────────────────────────────────────────────

def get_challenge_code(username, choice):
    print()
    print_warning("Instagram is requesting a security verification code (OTP).")
    if choice == ChallengeChoice.SMS:
        return prompt("Enter the OTP sent to your phone (SMS): ")
    elif choice == ChallengeChoice.EMAIL:
        return prompt("Enter the OTP sent to your email: ")
    return prompt("Enter the OTP code sent by Instagram: ")

def login_instagram():
    cl = Client()
    cl.delay_range = [0, 1]
    cl.challenge_code_handler = get_challenge_code
    
    if os.path.exists(SESSION_FILE):
        print_step("Found saved session! Logging in automatically...")
        try:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            print_success("Auto-login successful!")
            return cl
        except Exception as e:
            print_warning("Saved session expired. Please log in again.")
            cl = Client()
            cl.delay_range = [0, 1]
            cl.challenge_code_handler = get_challenge_code
            
    print_header("LOGIN")
    username = prompt("Instagram Username: ")
    password = prompt("Instagram Password: ")
    
    print_step("Logging in (this may take a few seconds)...")
    try:
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print_success("Login successful! Session saved for next time.")
        return cl
    except TwoFactorRequired:
        print_warning("Two-Factor Authentication (2FA) is enabled.")
        code = prompt("Enter the 2FA code: ")
        try:
            cl.login(username, password, verification_code=code)
            cl.dump_settings(SESSION_FILE)
            print_success("2FA Login successful! Session saved.")
            return cl
        except Exception as e:
            print_error(f"2FA Login failed: {e}")
            return None
    except ChallengeRequired as e:
        print_error("Instagram blocked the login (suspicious activity).")
        print_info("Open the Instagram app on your phone and approve the login.")
        return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None

# ─── Download Logic ───────────────────────────────────────────

def download_single_media(cl, media_pk, media_type, download_dir):
    try:
        # 1. Smart History check: Even if the user deletes the file, we remember it was downloaded
        if str(media_pk) in downloaded_history:
            return True
            
        # 2. Folder check: Just in case it's in the folder but not in history
        if os.path.exists(download_dir):
            for fname in os.listdir(download_dir):
                if str(media_pk) in fname:
                    downloaded_history.add(str(media_pk))
                    save_history(downloaded_history)
                    return True
                    
        # Small delay to avoid triggering Instagram's rate limits/bot detection
        time.sleep(1.5)
        
        # Always fetch via private API to avoid the public JSONDecodeError HTML block
        try:
            media_info = cl.media_info_v1(media_pk)
            # Inject into cache so the download methods don't try public requests
            cl._medias_cache[media_pk] = media_info 
            media_type = media_info.media_type
        except Exception:
            # If private API fails, it might be deleted or we are rate limited.
            pass
            
        if media_type == 1:
            cl.photo_download(media_pk, folder=download_dir)
        elif media_type == 2:
            cl.video_download(media_pk, folder=download_dir)
        elif media_type == 8:
            cl.album_download(media_pk, folder=download_dir)
            
        # Add to smart history and save
        downloaded_history.add(str(media_pk))
        save_history(downloaded_history)
        
        return True
    except Exception as e:
        return False

def download_chat_media(cl, chat_name, download_dir="downloads"):
    print_header(f"CHAT: {chat_name}")
    os.makedirs(download_dir, exist_ok=True)
    
    print_step("Searching for chat...")
    threads = cl.direct_threads(amount=30)
    
    target_thread = None
    for thread in threads:
        if thread.thread_title and chat_name.lower() in thread.thread_title.lower():
            target_thread = thread
            break
        elif any(chat_name.lower() in u.username.lower() for u in thread.users):
            target_thread = thread
            break
            
    if not target_thread:
        print_error(f"Chat '{chat_name}' not found in recent threads.")
        return
        
    title = target_thread.thread_title or ", ".join([u.username for u in target_thread.users])
    print_success(f"Found chat: {Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}")
    
    CACHE_FILE = f"chat_cache_{target_thread.id}.pkl"
    messages = []
    
    if os.path.exists(CACHE_FILE):
        print_step("Loading messages from local cache (super fast!)...")
        with open(CACHE_FILE, 'rb') as f:
            messages = pickle.load(f)
        print_success(f"Loaded {Fore.WHITE}{Style.BRIGHT}{len(messages)}{Style.RESET_ALL}{Fore.GREEN} messages from cache.")
    else:
        print_step("Fetching ALL messages (going back 4+ years)...")
        print_info("This may take several minutes for large chats. Don't close the window!\n")
        
        original_private_request = cl.private_request
        fetch_state = {"count": 0, "start": time.time()}
        
        def patched_request(endpoint, *args, **kwargs):
            result = original_private_request(endpoint, *args, **kwargs)
            if "direct_v2/threads/" in endpoint and "thread" in result:
                fetch_state["count"] += len(result["thread"].get("items", []))
                elapsed = time.time() - fetch_state["start"]
                print(f"\r  {Fore.CYAN}⏳{Style.RESET_ALL} Loaded {Fore.WHITE}{Style.BRIGHT}{fetch_state['count']}{Style.RESET_ALL} messages... ({elapsed:.0f}s elapsed)", end="", flush=True)
            return result
        
        cl.private_request = patched_request
        
        start_time = time.time()
        messages = cl.direct_messages(target_thread.id, amount=100000)
        fetch_time = time.time() - start_time
        
        cl.private_request = original_private_request
        
        print(f"\n")
        print_success(f"Fetched {Fore.WHITE}{Style.BRIGHT}{len(messages)}{Style.RESET_ALL}{Fore.GREEN} messages in {fetch_time:.0f} seconds.")
        
        # Save to cache so we never wait 14 minutes again
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(messages, f)
            
    print_step("Scanning for reels, posts, and links...\n")
    
    # Phase 1: Collect all media
    media_to_download = []
    
    for msg in messages:
        try:
            media_pk = None
            media_type = None
            
            # Universal brute-force finder: dump message to string and regex for instagram urls
            # This perfectly catches the new 'xma_clip' and 'xma_media_share' formats 
            # without worrying about exactly where Instagram nested the target_url
            msg_str = str(msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict())
            
            # Find any instagram post/reel URL
            urls = re.findall(r'(https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+/?)', msg_str)
            if urls:
                try:
                    media_pk = cl.media_pk_from_url(urls[0])
                except Exception:
                    pass
            
            # Fallback to old direct properties just in case
            if not media_pk:
                if msg.item_type in ["media_share", "clip", "felix_share"]:
                    if hasattr(msg, 'media_share') and msg.media_share:
                        media_pk = msg.media_share.pk
                        media_type = msg.media_share.media_type
                    elif hasattr(msg, 'clip') and msg.clip:
                        clip_media = msg.clip
                        if hasattr(clip_media, 'clip') and clip_media.clip:
                            media_pk = clip_media.clip.pk
                            media_type = clip_media.clip.media_type
                        elif hasattr(clip_media, 'pk'):
                            media_pk = clip_media.pk
                            media_type = getattr(clip_media, 'media_type', 2)
                    elif hasattr(msg, 'felix_share') and msg.felix_share:
                        felix = msg.felix_share
                        if hasattr(felix, 'video') and felix.video:
                            media_pk = felix.video.pk
                            media_type = felix.video.media_type
                        elif hasattr(felix, 'pk'):
                            media_pk = felix.pk
                            media_type = getattr(felix, 'media_type', 2)
                
                elif msg.item_type == "story_share":
                    if hasattr(msg, 'story_share') and msg.story_share:
                        story = msg.story_share
                        if hasattr(story, 'media') and story.media:
                            media_pk = story.media.pk
                            media_type = story.media.media_type
                
                elif msg.item_type == "raven_media":
                    if hasattr(msg, 'visual_media') and msg.visual_media:
                        vm = msg.visual_media
                        if hasattr(vm, 'media') and vm.media:
                            if hasattr(vm.media, 'pk'):
                                media_pk = vm.media.pk
                                media_type = getattr(vm.media, 'media_type', 2)



            if media_pk:
                if not any(m[0] == media_pk for m in media_to_download):
                    media_to_download.append((media_pk, media_type))
                    
        except Exception:
            pass
    
    total = len(media_to_download)
    print_success(f"Found {Fore.WHITE}{Style.BRIGHT}{total}{Style.RESET_ALL}{Fore.GREEN} unique media items to download!")
    
    if total == 0:
        print_info("No media found in this chat.")
        return
    
    # Phase 2: Download
    print_step(f"Downloading with 4 parallel threads...\n")
    
    download_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for media_pk, media_type in media_to_download:
            future = executor.submit(download_single_media, cl, media_pk, media_type, download_dir)
            futures[future] = media_pk
        
        for i, future in enumerate(as_completed(futures), 1):
            media_pk = futures[future]
            try:
                success = future.result()
                if success:
                    download_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
            print_progress(i, total, str(media_pk))

    print("\n")
    
    abs_path = os.path.abspath(download_dir)
    print_summary_box("DOWNLOAD COMPLETE", [
        f"Chat:       {title}",
        f"Downloaded: {download_count} items",
        f"Skipped:    {failed_count} items",
        f"Total:      {total} items found",
        f"",
        f"Saved to: {abs_path}",
    ])

# ─── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        os.system("title Instagram Chat Media Downloader")
        banner()
        cl = login_instagram()
        
        if cl:
            config = load_config()
            saved_chats = config.get("last_chats", [])
            
            if saved_chats:
                print_info(f"Last used chats: {Fore.WHITE}{Style.BRIGHT}{', '.join(saved_chats)}{Style.RESET_ALL}")
                use_saved = prompt("Press Enter to reuse, or type new chat names: ").strip()
                if use_saved:
                    chat_names = [name.strip() for name in use_saved.split(',')]
                else:
                    chat_names = saved_chats
            else:
                chat_names_input = prompt("Target Chat Names (comma-separated): ")
                chat_names = [name.strip() for name in chat_names_input.split(',')]
            
            config["last_chats"] = [c for c in chat_names if c]
            save_config(config)
            
            for chat_name in chat_names:
                if chat_name:
                    download_chat_media(cl, chat_name)
            
            print(f"\n  {Fore.GREEN}{Style.BRIGHT}🎉 All tasks completed!{Style.RESET_ALL}")
    except Exception as e:
        print_error("An unexpected error occurred:")
        traceback.print_exc()
    
    print(f"\n{'─' * 56}")
    prompt("Press Enter to close this window...")
