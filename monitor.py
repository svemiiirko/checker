import json
import os
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL = "https://szztk.ba/"
KEYWORD = "samozapošljavanja"
STATE_FILE = "seen_links.json"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def load_seen_links():
    """Loads previously notified links from a JSON file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Error loading state file: {e}")
            return set()
    return set()


def save_seen_links(seen_links):
    """Saves updated links back to the JSON file."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_links), f, indent=2)
    except Exception as e:
        print(f"Error saving state file: {e}")


def send_email(new_matches):
    """Sends a single consolidated email for all newly found items."""
    body_items = "\n\n".join(
        f"- {title}\n  Link: {link}" for title, link in new_matches
    )
    subject = f"Alert: {len(new_matches)} new post(s) found for '{KEYWORD}'"
    body = (
        f"New content containing '{KEYWORD}' was published on {URL}:\n\n"
        f"{body_items}\n\n"
        f"Direct Website: {URL}"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def check_website():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    seen_links = load_seen_links()
    new_matches = []

    # Find all links on the page
    for a_tag in soup.find_all("a", href=True):
        link_text = a_tag.get_text(strip=True)
        href = a_tag["href"]
        full_url = urljoin(URL, href)

        # Check if keyword is in the link text or surrounding article title
        if KEYWORD.lower() in link_text.lower():
            if full_url not in seen_links:
                new_matches.append((link_text or "New Announcement", full_url))
                seen_links.add(full_url)

    if new_matches:
        print(f"Found {len(new_matches)} new item(s)!")
        send_email(new_matches)
        save_seen_links(seen_links)
    else:
        print(f"No new items containing '{KEYWORD}' found.")


if __name__ == "__main__":
    check_website()
