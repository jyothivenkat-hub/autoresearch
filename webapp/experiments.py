"""Experiment engine — runs content experiments via Claude API."""

import os
import json
import time
from dotenv import load_dotenv
import anthropic

load_dotenv()

MODEL = "claude-sonnet-4-20250514"

EXPERIMENTS = [
    {
        "name": "original_post_topics",
        "description": "Generate original posts on trending AI topics",
        "prompt": """Based on the profile analysis below, generate 5 original tweet ideas that would maximize impressions and followers.

Each tweet should:
- Use patterns that worked: include numbers, emojis, conversational tone
- Be 50-200 characters
- Feel authentic to the voice in the top posts

For each tweet, explain WHY it should work based on the data patterns.

Format as JSON array:
[{{"tweet": "...", "reasoning": "...", "predicted_metric": "impressions|follows|engagement", "confidence": "high|medium|low"}}]"""
    },
    {
        "name": "reply_strategies",
        "description": "Generate high-impact reply templates for big accounts",
        "prompt": """Based on the profile analysis, generate 5 reply strategies for big accounts in the user's niche.

For each, provide:
1. A template reply for when they post about their topic
2. A template reply for when they share a product/launch
3. Tips on timing and tone

The replies should feel genuine and add value.

Format as JSON array:
[{{"target": "@handle", "topic_reply": "...", "launch_reply": "...", "tips": "..."}}]"""
    },
    {
        "name": "engagement_hooks",
        "description": "Test different hook styles for original posts",
        "prompt": """Generate 5 variations of a SINGLE topic relevant to the user using different hook styles.

Variations to test:
1. Question hook ("Have you ever...?")
2. Number hook ("3 things I learned...")
3. Contrarian hook ("Everyone says X, but...")
4. Story hook ("I just realized...")
5. Milestone hook ("Just hit X...")

For each, write the full tweet (under 280 chars) and predict which metrics it optimizes.

Format as JSON array:
[{{"style": "...", "tweet": "...", "optimizes_for": "impressions|follows|engagement", "reasoning": "..."}}]"""
    },
    {
        "name": "follower_conversion",
        "description": "Posts optimized specifically for follower growth",
        "prompt": """Generate 10 tweet ideas specifically optimized for FOLLOWER GROWTH.

Strategies to use:
- Personal connection ("Hey! I'm...")
- Value proposition ("Follow me for...")
- Social proof ("Just hit X...")
- Community building ("Who else is...")
- Vulnerability/authenticity ("Honestly, I...")

Each should feel natural and authentic.

Format as JSON array:
[{{"tweet": "...", "strategy": "...", "reasoning": "..."}}]"""
    },
    {
        "name": "viral_reply_formulas",
        "description": "Reusable reply templates that go viral",
        "prompt": """Generate 10 reply templates that could work on ANY big account's post.

Categories:
- Humor/wit
- Adding unique insight
- Personal story that relates
- Contrarian but respectful take
- Asking a smart follow-up question

For each template, include [PLACEHOLDER] for context.

Format as JSON array:
[{{"category": "...", "template": "...", "example_usage": "...", "why_it_works": "..."}}]"""
    },
    {
        "name": "weekly_plan",
        "description": "Optimized 7-day posting schedule",
        "prompt": """Create an optimal weekly posting plan based on the data patterns.

Consider day-of-week performance, optimal mix of originals vs replies, and content themes.

Format as JSON:
{{"weekly_plan": [{{"day": "Monday", "originals": N, "replies": N, "themes": ["..."], "strategy": "..."}}], "best_times": ["..."], "key_tactics": ["..."]}}"""
    },
    {
        "name": "ab_test_posts",
        "description": "A/B test variations of top posts",
        "prompt": """Take the top 3 performing posts from the profile and create A/B test variations.

For each, create 3 variations testing:
A) Different opening hook
B) Different length
C) Different call-to-action

Predict which variation would outperform.

Format as JSON array:
[{{"original": "...", "variation_a": "...", "variation_b": "...", "variation_c": "...", "prediction": "..."}}]"""
    },
]


def get_experiment_list():
    return [{"name": e["name"], "description": e["description"]} for e in EXPERIMENTS]


def run_experiment(experiment_name, profile_text):
    """Run a single experiment. Returns dict with result and timing."""
    exp = next((e for e in EXPERIMENTS if e["name"] == experiment_name), None)
    if not exp:
        return {"status": "error", "message": f"Unknown experiment: {experiment_name}"}

    client = anthropic.Anthropic()
    full_prompt = f"{profile_text}\n\n---\n\n{exp['prompt']}"

    t0 = time.time()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}],
        )
        result_text = response.content[0].text
        dt = time.time() - t0

        # Try to extract JSON
        json_start = result_text.find('[') if '[' in result_text else result_text.find('{')
        json_end = max(result_text.rfind(']'), result_text.rfind('}')) + 1
        parsed = None
        if json_start >= 0 and json_end > json_start:
            try:
                parsed = json.loads(result_text[json_start:json_end])
            except json.JSONDecodeError:
                pass

        return {
            "status": "success",
            "name": exp["name"],
            "description": exp["description"],
            "data": parsed,
            "raw": result_text,
            "time_seconds": round(dt, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "name": exp["name"],
            "description": exp["description"],
            "message": str(e),
            "time_seconds": round(time.time() - t0, 1),
        }


def run_custom_experiment(prompt, profile_text):
    """Run a custom experiment with a user-provided prompt."""
    client = anthropic.Anthropic()
    full_prompt = f"{profile_text}\n\n---\n\n{prompt}\n\nFormat your response as a JSON array."

    t0 = time.time()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}],
        )
        result_text = response.content[0].text
        dt = time.time() - t0

        json_start = result_text.find('[') if '[' in result_text else result_text.find('{')
        json_end = max(result_text.rfind(']'), result_text.rfind('}')) + 1
        parsed = None
        if json_start >= 0 and json_end > json_start:
            try:
                parsed = json.loads(result_text[json_start:json_end])
            except json.JSONDecodeError:
                pass

        return {
            "status": "success",
            "name": "custom",
            "description": "Custom experiment",
            "data": parsed,
            "raw": result_text,
            "time_seconds": round(dt, 1),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "time_seconds": round(time.time() - t0, 1)}
