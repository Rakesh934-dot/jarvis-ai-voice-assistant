
import subprocess
import re
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus

# Mac applications
APP_ALIASES = {
    "safari": "Safari",
    "finder": "Finder",
    "terminal": "Terminal",
    "notes": "Notes",
    "calculator": "Calculator",
    "calendar": "Calendar",
    "settings": "System Settings",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "spotify": "Spotify",
}

# Websites
WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
}


def time_answer():
    return (
        f"Rakesh, the time is "
        f"{datetime.now().strftime('%I:%M %p')}."
    )


def date_answer():
    return (
        f"Today is "
        f"{datetime.now().strftime('%A, %B %d, %Y')}."
    )


def open_app(app_name):
    try:
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"Opening {app_name}, Rakesh."

        return f"Rakesh, I could not open {app_name}."

    except Exception as error:
        print(f"App error: {error}")
        return f"Sorry Rakesh, I could not open {app_name}."


def open_website(url):
    try:
        if webbrowser.open(url):
            return "Opening the website, Rakesh."

        return "Sorry Rakesh, I could not open the website."

    except Exception as error:
        print(f"Website error: {error}")
        return "Sorry Rakesh, I could not open the website."


def search_google(query):
    query = query.strip()

    if not query:
        return "Rakesh, what should I search for?"

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    if webbrowser.open(url):
        return f"Searching Google for {query}, Rakesh."

    return "Sorry Rakesh, I could not open Google."


def search_youtube(query):
    query = query.strip()

    if not query:
        return open_website(WEBSITES["youtube"])

    url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    if webbrowser.open(url):
        return f"Searching YouTube for {query}, Rakesh."

    return "Sorry Rakesh, I could not open YouTube."


def handle_command(command):
    text = command.lower().strip()
    text = text.rstrip(" .!?")

    if not text:
        return None

    # JARVIS identity
    if text in (
        "who are you",
        "what is your name",
        "what's your name",
        "tell me your name",
    ):
        return (
            "I am Jarvis, Rakesh's personal AI assistant. "
            "I am here to help you."
        )

    if text in (
        "what is my name",
        "what's my name",
        "who am i",
    ):
        return "Your name is Rakesh."

    # Time commands
    if text in (
        "time",
        "what time is it",
        "what time is it now",
        "tell me the time",
        "current time",
    ):
        return time_answer()

    # Date commands
    if text in (
        "date",
        "today",
        "today's date",
        "what is today's date",
        "what is the date today",
        "tell me today's date",
    ):
        return date_answer()

    # YouTube search
    youtube_prefixes = (
        "open youtube and search for ",
        "search youtube for ",
        "search on youtube for ",
        "play on youtube ",
    )

    for prefix in youtube_prefixes:
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            return search_youtube(query)

    youtube_match = re.fullmatch(
        r"(?:search(?: for)?|find|look up)\s+(.+?)\s+"
        r"(?:on|in)\s+youtube",
        text
    )

    if youtube_match:
        return search_youtube(youtube_match.group(1))

    # Google search
    google_match = re.fullmatch(
        r"(?:search(?: google)?(?: for)?|google)\s+(.+)",
        text
    )

    if google_match:
        return search_google(google_match.group(1))

    # Open websites
    for name, url in WEBSITES.items():
        if text in (
            f"open {name}",
            f"launch {name}",
            f"go to {name}",
        ):
            return open_website(url)

    # Open applications
    for alias, app_name in APP_ALIASES.items():
        if text in (
            alias,
            f"open {alias}",
            f"launch {alias}",
            f"start {alias}",
        ):
            return open_app(app_name)

    # Music commands
    if text in (
        "open music",
        "play music",
        "open spotify",
        "launch spotify",
    ):
        return open_app("Spotify")

    # IMPORTANT:
    # Unknown commands must go to the AI brain.
    return None


if __name__ == "__main__":
    print("JARVIS Fixed Commands Test")
    print("Type 'quit' to exit.")

    while True:
        command = input("You: ").strip()

        if command.lower() in ("quit", "exit"):
            print("Goodbye Rakesh.")
            break

        result = handle_command(command)

        if result is None:
            print("Jarvis: Sending this question to AI brain.")
        else:
            print("Jarvis:", result)
