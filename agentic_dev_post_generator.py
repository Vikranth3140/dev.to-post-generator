import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

DEV_API_KEY = os.getenv("DEV_API_KEY")
OLLAMA_URL = "http://localhost:11434/api/generate"

HEADERS = {
    "api-key": DEV_API_KEY,
    "Content-Type": "application/json"
}


def fetch_my_articles():
    print("📡 Fetching your DEV.to articles...")
    resp = requests.get("https://dev.to/api/articles/me", headers=HEADERS)
    if resp.status_code != 200:
        print("❌ Error:", resp.text)
        return []
    articles = resp.json()
    print(f"✅ Retrieved {len(articles)} articles.")
    with open("my_articles.json", "w") as f:
        json.dump(articles, f, indent=2)
    return articles


def summarize_top_articles(articles, top_n=3):
    print("🧮 Summarizing top-performing articles...")
    sorted_articles = sorted(articles, key=lambda x: x.get("public_reactions_count", 0), reverse=True)
    summary = []
    for article in sorted_articles[:top_n]:
        summary.append(
            f"Title: {article.get('title', 'No Title')}\nTags: {', '.join(article.get('tags', []))}\nReactions: {article.get('public_reactions_count', 0)}\n--\n{article.get('description', '')}"
        )
    print("✅ Summary prepared for DeepSeek prompt.")
    return "\n\n".join(summary)


def ask_deepseek(prompt):
    print("🤖 Sending prompt to DeepSeek model...")
    payload = {
        "model": "deepseek-r1:7b",
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload)
    if resp.status_code != 200:
        print("❌ DeepSeek request failed:", resp.text)
        return ""
    print("✅ Response received from DeepSeek.")
    return resp.json().get("response", "")


def generate_blog_draft(top_summary):
    react_prompt = f"""
You are a helpful blogging assistant. Based on the following successful blog post summaries:

{top_summary}

Think step-by-step:
1. What themes or tags perform well?
2. What kind of topic should we write next?
3. Generate a DEV.to-compatible markdown post on that topic.
4. Output the title, tags, and markdown content.

Format:
Title: <title>
Tags: [tag1, tag2, ...]
---markdown---
<markdown>
"""
    return ask_deepseek(react_prompt)


def write_draft_file(response_text):
    print("📝 Parsing response from DeepSeek...")
    parts = response_text.split("---markdown---")
    if len(parts) != 2:
        print("⚠️ DeepSeek response format unexpected:")
        print(response_text)  # Print raw response
        raise ValueError("Unexpected response format from DeepSeek.")
    header, markdown = parts
    with open("draft_post.md", "w", encoding="utf-8") as f:
        f.write(markdown.strip())
    print("✅ Draft saved as draft_post.md")
    return header, markdown.strip()


def prompt_user_action():
    print("\n💬 Choose an option:")
    print("[1] Publish draft to DEV.to")
    print("[2] Edit slightly (provide a prompt)")
    print("[3] Redo completely (provide new topic)")
    return input("Enter 1, 2, or 3: ").strip()


def publish_article(title, markdown):
    print("🚀 Publishing article as a draft on DEV.to...")
    payload = {
        "article": {
            "title": title,
            "published": False,
            "body_markdown": markdown
        }
    }
    res = requests.post("https://dev.to/api/articles", headers=HEADERS, json=payload)
    if res.status_code == 201:
        print("🎉 Draft published to DEV.to!")
    else:
        print("❌ Failed to publish:", res.text)


if __name__ == "__main__":
    if not DEV_API_KEY:
        raise ValueError("Set your DEV_API_KEY in a .env file!")

    articles = fetch_my_articles()
    if not articles:
        exit()

    summary = summarize_top_articles(articles)
    deepseek_response = generate_blog_draft(summary)
    title_line, markdown = write_draft_file(deepseek_response)
    print("\n📄 Generated Post:")
    print(title_line)

    choice = prompt_user_action()

    if choice == "1":
        publish_article(title_line.replace("Title: ", "").strip(), markdown)
    elif choice == "2":
        edit_prompt = input("✏️ Enter what you want the assistant to tweak: ")
        new_prompt = summary + f"\n\nUser wants this edited: {edit_prompt}\nNow generate again."
        new_response = generate_blog_draft(new_prompt)
        write_draft_file(new_response)
    elif choice == "3":
        new_topic = input("🧠 Enter new topic and any guidance: ")
        redo_prompt = f"Write a DEV.to blog post from scratch on this topic: {new_topic}. Follow same output format."
        redo_response = ask_deepseek(redo_prompt)
        write_draft_file(redo_response)
    else:
        print("🚫 No action taken.")
