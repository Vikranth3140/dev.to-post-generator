import requests
import os
import json
from dotenv import load_dotenv
import time

load_dotenv()

DEV_API_KEY = os.getenv("DEV_API_KEY")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Configurable model selection
REASONING_MODEL = "llama3.1"  # Options: deepseek, mistral, llama3.1
GENERATION_MODEL = "mistral"   # Options: mistral, llama3.1
VALIDATION_MODEL = "llama3.1"  # Model to validate factual correctness
IMAGE_SEARCH_MODEL = "llama3.1"  # Model with imagined access to image suggestions

HEADERS = {
    "api-key": DEV_API_KEY,
    "Content-Type": "application/json"
}


def call_ollama(prompt, model_name):
    print(f"🤖 Sending prompt to {model_name} via Ollama...")
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload)
    if resp.status_code != 200:
        print(f"❌ Ollama request failed ({model_name}):", resp.text)
        return ""
    print(f"✅ Response received from {model_name}.")
    return resp.json().get("response", "")


def summarize_individual_post(article):
    title = article.get('title', '')
    tags = ', '.join(article.get('tags', []))
    description = article.get('description', '')
    body_markdown = article.get('body_markdown', '')[:2000]

    prompt = f"""
Summarize the following blog post in 4-5 lines.
Include its core topic, style, target audience, and why it likely performed well.

Title: {title}
Tags: {tags}
Description: {description}

Content:
{body_markdown}
"""
    return call_ollama(prompt, REASONING_MODEL)


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
2. Generate a long and detailed markdown article in this exact format:

Title: <title>
Tags: [tag1, tag2, ...]
---markdown---
<markdown content>

Requirements:
- Write in markdown style using proper headers, code blocks, lists, and bold/italic where appropriate.
- Include examples, code snippets, or diagrams if applicable.
- Make the article informative and actionable, not just theoretical.
- Avoid including any commentary or explanation outside the specified format.

ONLY return the blog post in the format above.
"""
    return call_ollama(prompt, GENERATION_MODEL)


def analyze_generated_post(post_text, previous_summaries):
    prompt = f"""
You are an expert content analyst. Review the following newly generated blog post:

{post_text}

Compare it with the following summaries of previous posts:

{previous_summaries}

1. Does this new post introduce a significantly different topic, or is it too similar to previous ones?
2. Justify why this post might attract high public interest and engagement.
3. Mention what makes the content fresh, useful, or timely compared to past content.
"""
    return call_ollama(prompt, REASONING_MODEL)


def validate_blog_facts(post_text):
    prompt = f"""
Please fact-check the following blog post for technical and factual accuracy. Highlight any inconsistencies, misleading claims, or incorrect assumptions. If it is correct, say "All facts check out."

Post:
{post_text}
"""
    return call_ollama(prompt, VALIDATION_MODEL)


def suggest_images_for_post(post_text):
    prompt = f"""
Based on the blog post content below, suggest 2-3 suitable themes or keywords that can be used to search for high-quality background or hero images for this post.

Post:
{post_text}

Only return a list like: ["keyword1", "keyword2", "keyword3"]
"""
    return call_ollama(prompt, IMAGE_SEARCH_MODEL)


def write_draft_file(response_text):
    print("📝 Parsing response from generator model...")
    parts = response_text.split("---markdown---")
    if len(parts) != 2:
        print("⚠️ Model response format unexpected:")
        print(response_text)
        with open("draft_fallback.md", "w", encoding="utf-8") as f:
            f.write(response_text)
        print("⚠️ Full output saved to draft_fallback.md for manual editing.")
        raise ValueError("Unexpected response format.")

    header, markdown = parts
    title_line = ""
    for line in header.strip().splitlines():
        if line.lower().startswith("title:"):
            title_line = line
            break

    if not title_line:
        print("⚠️ Could not extract title line from response header.")
        title_line = "Title: Untitled"

    with open("draft_post.md", "w", encoding="utf-8") as f:
        f.write(markdown.strip())
    print("✅ Draft saved as draft_post.md")
    return title_line, markdown.strip()


def prompt_user_action():
    print("\n💬 Choose an option:")
    print("[1] Publish draft to DEV.to")
    print("[2] Edit slightly (provide a prompt)")
    print("[3] Redo completely (provide new topic)")
    print("[4] Save to DEV.to as draft (only visible in your profile)")
    print("[5] Exit")
    return input("Enter 1, 2, 3, 4, or 5: ").strip()


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


def publish_article(title, markdown, publish=False):
    print("🚀 Uploading article to DEV.to...")
    payload = {
        "article": {
            "title": title,
            "published": publish,
            "body_markdown": markdown
        }
    }
    res = requests.post("https://dev.to/api/articles", headers=HEADERS, json=payload)
    if res.status_code == 201:
        print("🎉 Article uploaded to DEV.to! Check your profile.")
    else:
        print("❌ Failed to upload:", res.text)


if __name__ == "__main__":
    if not DEV_API_KEY:
        raise ValueError("Set your DEV_API_KEY in a .env file!")

    articles = fetch_my_articles()
    if not articles:
        exit()

    while True:
        post_summaries = get_post_summaries(articles)
        ollama_response = generate_blog_draft_from_summaries(post_summaries)
        title_line, markdown = write_draft_file(ollama_response)
        print("\n📄 Generated Post:")
        print(title_line)

        analysis = analyze_generated_post(ollama_response, post_summaries)
        print("\n🔍 Post Analysis:")
        print(analysis)

        validation = validate_blog_facts(ollama_response)
        print("\n✅ Fact Check:")
        print(validation)

        image_suggestions = suggest_images_for_post(ollama_response)
        print("\n🖼️ Suggested Image Keywords:")
        print(image_suggestions)

        choice = prompt_user_action()

        if choice == "1":
            publish_article(title_line.replace("Title: ", "").strip(), markdown, publish=True)
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

Requirements:
- Write in markdown style using proper headers, code blocks, lists, and bold/italic where appropriate.
- Include examples, code snippets, or diagrams if applicable.
- Make the article informative and actionable, not just theoretical.
- Avoid including any commentary or explanation outside the specified format.
"""
            redo_response = call_ollama(redo_prompt, GENERATION_MODEL)
            write_draft_file(redo_response)
        elif choice == "4":
            publish_article(title_line.replace("Title: ", "").strip(), markdown, publish=False)
        elif choice == "5":
            print("👋 Exiting... Goodbye!")
            break
        else:
            print("🚫 No action taken.")
