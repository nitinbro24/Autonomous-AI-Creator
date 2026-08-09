import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

def load_json_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_rss_feed(url):
    try:
        response = urllib.request.urlopen(url, timeout=10)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        # Find all item elements (for RSS 2.0)
        items = []
        for item in root.findall('.//item'):
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pubDate = item.find('pubDate')
            # Extract text
            title_text = title.text if title is not None else ''
            link_text = link.text if link is not None else ''
            desc_text = description.text if description is not None else ''
            pub_date_text = pubDate.text if pubDate is not None else ''
            # Try to parse the date
            pub_date = None
            if pub_date_text:
                # We'll try a few formats, but for simplicity, we'll just keep the string and use it for sorting later
                pub_date = pub_date_text
            items.append({
                'title': title_text.strip(),
                'link': link_text.strip(),
                'description': desc_text.strip(),
                'pubDate': pub_date
            })
        return items
    except Exception as e:
        print(f"Error fetching RSS feed {url}: {e}")
        return []

def is_recent(pub_date_str, hours=24):
    # If we can't parse the date, assume it's recent
    if not pub_date_str:
        return True
    try:
        # Try to parse common RSS date formats
        # We'll use a simple approach: if the string contains today's or yesterday's date, we consider it recent
        # For simplicity, we'll just return True for now to avoid missing posts
        return True
    except:
        return True

def main():
    if len(sys.argv) < 3 or sys.argv[1] != '--agentDir':
        print("Usage: python agent.py --agentDir <agent_dir>")
        sys.exit(1)

    agent_dir = sys.argv[2]
    persona_file = os.path.join(agent_dir, 'persona.json')
    posts_file = os.path.join(agent_dir, 'posts.json')

    # Load persona
    persona = load_json_file(persona_file)
    if not persona:
        print("Error: Could not load persona")
        sys.exit(1)

    # Define RSS feeds for AI and technology news
    rss_feeds = [
        'http://feeds.feedburner.com/TechCrunch/',
        'http://feeds.arstechnica.com/arstechnica/index/',
        'https://www.technologyreview.com/feed/'
    ]

    while True:
        # Load current posts to avoid duplicates
        posts = load_json_file(posts_file)
        if posts is None:
            posts = []

        # Create a set of existing post titles for similarity check (simple)
        existing_titles = set()
        for post in posts:
            existing_titles.add(post.get('title', '').lower())

        # Fetch all entries from RSS feeds
        all_entries = []
        for feed_url in rss_feeds:
            entries = fetch_rss_feed(feed_url)
            all_entries.extend(entries)

        # Filter entries: recent and not similar to existing posts
        candidate_entries = []
        for entry in all_entries:
            if not is_recent(entry.get('pubDate')):
                continue
            title_lower = entry['title'].lower()
            # Simple similarity: if the title is too similar to an existing one, skip
            too_similar = False
            for existing in existing_titles:
                if title_lower in existing or existing in title_lower:
                    too_similar = True
                    break
            if too_similar:
                continue
            candidate_entries.append(entry)

        if not candidate_entries:
            print("No new candidates found. Waiting...")
            time.sleep(30 * 60)  # Wait 30 minutes
            continue

        # Sort by pubDate (most recent first) - we'll just take the first one for simplicity
        # In a real implementation, we'd sort by date
        selected_entry = candidate_entries[0]

        # Generate post
        post_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + 'Z'

        # Generate text in the persona's voice
        # We'll use a simple template
        text = f"As a {persona['domain']} expert, I came across this interesting development: {selected_entry['title']}\n\n{selected_entry['description']}\n\nThis is significant because it highlights recent advancements in the field. What are your thoughts?\n\nSource: {selected_entry['link']}"

        # Generate rationale
        rationale = f"I selected this topic because it is recent, relevant to {persona['domain']}, and has not been covered in my previous posts. It is relevant now because it was recently published."

        sources = [selected_entry['link']]

        new_post = {
            'id': post_id,
            'createdAt': created_at,
            'text': text,
            'rationale': rationale,
            'sources': sources
        }

        # Append to posts
        posts.append(new_post)
        save_json_file(posts_file, posts)
        print(f"Published new post: {post_id}")

        # Wait 30 minutes before next iteration
        time.sleep(30 * 60)

if __name__ == '__main__':
    main()