# DEV.to Post Generator

This project is an AI-powered assistant for generating high-quality, engaging blog posts for [DEV.to](https://dev.to/). It leverages multiple LLMs (via Ollama) for reasoning, content generation, validation, and image suggestion, and integrates with the DEV.to API for publishing.

## Features

- **Fetches your DEV.to articles** and analyzes top-performing posts.
- **Summarizes** previous articles to extract themes, styles, and gaps.
- **Generates new blog drafts** in markdown, tailored for high engagement.
- **Analyzes and validates** generated content for novelty and factual accuracy.
- **Suggests image keywords** for visual enhancement.
- **Human-in-the-loop options**: review, edit, or publish drafts directly or as a draft on DEV.to.

## Setup

1. **Clone the repository** and install dependencies:
   ```sh
   git clone https://github.com/Vikranth3140/dev.to-post-generator.git
   cd dev.to-post-generator
   pip install -r requirements.txt
   ```
2. **Set up your environment variables**:
   - Create a `.env` file in the project root:
     ```
     DEV_API_KEY=your_dev_to_api_key
     ```
   - [Get your DEV.to API key here](https://dev.to/settings/account).
3. **Start your Ollama server** and ensure the required models (`llama3.1`, `mistral`, etc.) are available and running.
   ```sh
    ollama run llama3.1
    ollama run mistral
   ```

## Usage

Run the main script:
```sh
python dev_post_generator.py
```

Follow the prompts to:
- Generate a new post draft based on your top articles.
- Review AI-generated analysis and fact-checking.
- Get suggested image keywords.
- Choose to publish, edit, redo, or save as a draft.

## Architecture: Modular, Not Multi-Agentic

This project uses a modular architecture, where each function (reasoning, generation, validation, image suggestion) is invoked by a central orchestrator script. While these modules are referred to as "agents" for clarity, they are not autonomous agents in the sense of multi-agent systems—they do not operate independently, maintain their own state, or communicate with each other outside the main script.

### Human-in-the-Loop Regulation

At each stage, the human user is prompted to:

- **Review** the generated draft, analysis, and fact-check results.
- **Edit** the draft with custom instructions, or request a complete redo.
- **Approve** and publish the post, or save it as a draft for further review.

This ensures that while AI modules automate content creation and validation, the final decision and oversight remain with the human user, providing a regulated, safe, and high-quality publishing workflow.

---

**Note:**  
This project does not implement a true multi-agentic system as defined in AI or distributed systems research. All "agents" are stateless model calls orchestrated by a single script, with no inter-agent communication or autonomy.