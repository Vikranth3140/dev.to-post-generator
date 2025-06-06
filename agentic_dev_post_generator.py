import requests
import os
import json
from dotenv import load_dotenv
import time

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


def ask_ollama(prompt):
    print("🤖 Sending prompt to Mistral via Ollama...")
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload)
    if resp.status_code != 200:
        print("❌ Ollama request failed:", resp.text)
        return ""
    print("✅ Response received from Mistral.")
    return resp.json().get("response", "")


def summarize_individual_post(article):
    title = article.get('title', '')
    tags = ', '.join(article.get('tags', []))
    description = article.get('description', '')
    body_markdown = article.get('body_markdown', '')[:2000]  # truncate if needed

    prompt = f"""
Summarize the following blog post in 4-5 lines.
Include its core topic, style, target audience, and why it likely performed well.

Title: {title}
Tags: {tags}
Description: {description}

Content:
{body_markdown}
"""
    return ask_ollama(prompt)


def get_post_summaries(articles, top_n=5):
    print("📚 Summarizing top articles one by one...")
    sorted_articles = sorted(articles, key=lambda x: x.get("public_reactions_count", 0), reverse=True)
    summaries = []
    for article in sorted_articles[:top_n]:
        summary = summarize_individual_post(article)
        summaries.append(summary)
        time.sleep(1)
    return "\n\n".join(summaries)


def generate_blog_draft_from_summaries(post_summaries):
    prompt = f"""
You are a blogging assistant. Based on the following summaries of previous successful DEV.to posts:

{post_summaries}

Analyze common themes, styles, and gaps. Then:
1. Propose a new high-performing topic.
2. Generate a markdown article in this exact format:

Title: <title>
Tags: [tag1, tag2, ...]
---markdown---
<markdown content>

Do NOT include <think> or explanations. Only return the formatted post.
"""
    return ask_ollama(prompt)


def write_draft_file(response_text):
    print("📝 Parsing response from Mistral...")
    parts = response_text.split("---markdown---")
    if len(parts) != 2:
        print("⚠️ Model response format unexpected:")
        print(response_text)
        with open("draft_fallback.md", "w", encoding="utf-8") as f:
            f.write(response_text)
        print("⚠️ Full output saved to draft_fallback.md for manual editing.")
        raise ValueError("Unexpected response format.")
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

    post_summaries = get_post_summaries(articles)
    ollama_response = generate_blog_draft_from_summaries(post_summaries)
    title_line, markdown = write_draft_file(ollama_response)
    print("\n📄 Generated Post:")
    print(title_line)

    choice = prompt_user_action()

    if choice == "1":
        publish_article(title_line.replace("Title: ", "").strip(), markdown)
    elif choice == "2":
        edit_prompt = input("✏️ Enter what you want the assistant to tweak: ")
        new_prompt = post_summaries + f"\n\nUser wants this edited: {edit_prompt}\nNow generate again."
        new_response = generate_blog_draft_from_summaries(new_prompt)
        write_draft_file(new_response)
    elif choice == "3":
        new_topic = input("🧠 Enter new topic and any guidance: ")
        redo_prompt = f"""
Write a DEV.to blog post from scratch on this topic: {new_topic}.

Respond using ONLY the following format:
Title: <title>
Tags: [comma, separated, tags]
---markdown---
<markdown content>

Do NOT include any explanations or commentary. Just return the post in the format above.
"""
        redo_response = ask_ollama(redo_prompt)
        write_draft_file(redo_response)
    else:
        print("🚫 No action taken.")
