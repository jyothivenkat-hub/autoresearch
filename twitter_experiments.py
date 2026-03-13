"""
Twitter Content Experiment Loop — autoresearch-style for social media.

Analyzes your top posts, runs experiments with Claude to generate optimized
variations, scores them, and finds what works best for impressions & followers.

Usage: python3 twitter_experiments.py
"""

import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Load and analyze Twitter data
# ---------------------------------------------------------------------------

DATA_PATH = "/Users/jv222/Downloads/account_analytics_content_2026-02-14_2026-03-13.csv"
RESULTS_PATH = "/Users/jv222/Documents/Projects/Auto Research/experiment_results.tsv"

def load_twitter_data():
    posts = []
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Impressions'] = int(row['Impressions'])
            row['Likes'] = int(row['Likes'])
            row['Engagements'] = int(row['Engagements'])
            row['New follows'] = int(row['New follows'])
            row['Bookmarks'] = int(row['Bookmarks'])
            row['Replies'] = int(row['Replies'])
            row['Reposts'] = int(row['Reposts'])
            posts.append(row)
    return posts


def get_top_posts(posts, metric='Impressions', n=15):
    return sorted(posts, key=lambda x: x[metric], reverse=True)[:n]


def get_original_posts(posts):
    return [p for p in posts if not str(p['Post text']).startswith('@')]


def get_replies(posts):
    return [p for p in posts if str(p['Post text']).startswith('@')]


def build_profile(posts):
    """Build a profile summary of what works."""
    originals = get_original_posts(posts)
    replies = get_replies(posts)
    top_imp = get_top_posts(posts, 'Impressions', 10)
    top_follows = get_top_posts(posts, 'New follows', 10)
    top_likes = get_top_posts(posts, 'Likes', 10)

    profile = f"""TWITTER PROFILE ANALYSIS (@jyothiwrites)
Account focus: AI tools, build in public, tech commentary
Active for ~2 weeks, {len(posts)} total posts

STATS:
- {len(originals)} original posts (avg {sum(p['Impressions'] for p in originals)/max(len(originals),1):.0f} impressions)
- {len(replies)} replies (avg {sum(p['Impressions'] for p in replies)/max(len(replies),1):.0f} impressions)

TOP 10 BY IMPRESSIONS:
"""
    for p in top_imp:
        text = str(p['Post text'])[:120]
        profile += f"- {p['Impressions']:,} imp | {p['Likes']} likes | {p['New follows']} follows | \"{text}\"\n"

    profile += "\nTOP 10 BY FOLLOWERS GAINED:\n"
    for p in top_follows:
        text = str(p['Post text'])[:120]
        profile += f"- {p['New follows']} follows | {p['Impressions']:,} imp | \"{text}\"\n"

    profile += "\nTOP 10 BY LIKES:\n"
    for p in top_likes:
        text = str(p['Post text'])[:120]
        profile += f"- {p['Likes']} likes | {p['Impressions']:,} imp | \"{text}\"\n"

    profile += """
KEY PATTERNS FOUND:
- Replies to big accounts (Karpathy, Sundarpichai, etc.) get massive impressions
- Posts with emojis: 304 avg imp vs 179 without
- Posts with links: 497 avg imp vs 166 without
- Posts with numbers: 381 avg imp vs 112 without
- Thursday is best day (419 avg imp)
- Personal greetings drive follows ("Hey!", "Hello")
- Milestone/celebration posts get high engagement
- Medium length (50-150 chars) performs best, but 280+ also works
- Conversational, authentic tone outperforms polished takes
"""
    return profile


# ---------------------------------------------------------------------------
# Experiment types
# ---------------------------------------------------------------------------

EXPERIMENTS = [
    {
        "name": "original_post_topics",
        "description": "Generate original posts on trending AI topics",
        "prompt": """Based on the profile analysis below, generate 5 original tweet ideas that would maximize impressions and followers.

Each tweet should:
- Be about AI/tech (the account's focus area)
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
        "prompt": """Based on the profile analysis, the account's best impressions come from replies to big accounts.

Generate 5 reply strategies for these target accounts:
- @karpathy (AI/ML researcher)
- @sundarpichai (Google CEO)
- @elonmusk (X/Tesla/SpaceX)
- @gregisenberg (startups/building)
- @AravSrinivas (Perplexity AI)

For each, provide:
1. A template reply for when they post about AI
2. A template reply for when they share a product/launch
3. Tips on timing and tone

The replies should feel genuine and add value (not just "great post!").

Format as JSON array:
[{{"target": "@handle", "ai_reply": "...", "launch_reply": "...", "tips": "..."}}]"""
    },
    {
        "name": "engagement_hooks",
        "description": "Test different hook styles for original posts",
        "prompt": """Analyze the top posts and generate 5 variations of a SINGLE topic using different hook styles.

Topic: "Building AI tools and shipping them publicly"

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
        "name": "time_and_format",
        "description": "Optimize posting schedule and format",
        "prompt": """Based on the data patterns, create an optimal weekly posting plan.

Consider:
- Thursday has highest avg impressions (419)
- The account posts ~19 posts/day on active days
- Replies drive more impressions than originals
- Mix of original content and strategic replies works

Create a 7-day plan with:
- How many posts per day
- Ratio of originals vs replies
- Best times to post (based on when big accounts are active)
- Topic themes per day

Format as JSON:
{{"weekly_plan": [{{"day": "Monday", "originals": N, "replies": N, "themes": ["..."], "strategy": "..."}}]}}"""
    },
    {
        "name": "ab_test_posts",
        "description": "A/B test variations of your best-performing posts",
        "prompt": """Take the top 3 performing posts from the profile and create A/B test variations.

For each original post, create 3 variations that test:
A) Different opening hook
B) Different length (shorter vs longer)
C) Different call-to-action or engagement prompt

Predict which variation would outperform the original and why.

Format as JSON array:
[{{"original": "...", "variation_a": "...", "variation_b": "...", "variation_c": "...", "prediction": "which wins and why"}}]"""
    },
    {
        "name": "follower_conversion",
        "description": "Posts optimized specifically for follower growth",
        "prompt": """The data shows personal greetings and milestone posts drive the most followers.

Generate 10 tweet ideas specifically optimized for FOLLOWER GROWTH (not impressions).

Strategies to use:
- Personal connection ("Hey! I'm Jyothi, I build...")
- Value proposition ("Follow me for daily AI tool reviews")
- Social proof ("Just hit X followers/impressions")
- Community building ("Who else is building with AI?")
- Vulnerability/authenticity ("Honestly, I'm new here and...")

Each should feel natural and authentic to the account's voice.

Format as JSON array:
[{{"tweet": "...", "strategy": "...", "reasoning": "..."}}]"""
    },
    {
        "name": "viral_reply_formulas",
        "description": "Analyze what makes replies go viral and generate templates",
        "prompt": """The account's top reply got 18,002 impressions ("69 mins? Hey learnt to say no!!").

Analyze what makes replies go viral and generate 10 reply templates that could work on ANY big account's post.

Categories:
- Humor/wit (like the 69 mins reply)
- Adding unique insight
- Personal story that relates
- Contrarian but respectful take
- Asking a smart follow-up question

For each template, include [PLACEHOLDER] for the specific context.

Format as JSON array:
[{{"category": "...", "template": "...", "example_usage": "...", "why_it_works": "..."}}]"""
    },
]


# ---------------------------------------------------------------------------
# Run experiments
# ---------------------------------------------------------------------------

def run_experiment(experiment, profile):
    """Run a single experiment using Claude."""
    print(f"\n{'='*60}")
    print(f"EXPERIMENT: {experiment['name']}")
    print(f"Description: {experiment['description']}")
    print(f"{'='*60}")

    full_prompt = f"{profile}\n\n---\n\n{experiment['prompt']}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}],
        )
        result = response.content[0].text

        # Try to extract JSON
        json_start = result.find('[') if '[' in result else result.find('{')
        json_end = max(result.rfind(']'), result.rfind('}')) + 1
        if json_start >= 0 and json_end > json_start:
            try:
                parsed = json.loads(result[json_start:json_end])
                return {"status": "success", "data": parsed, "raw": result}
            except json.JSONDecodeError:
                pass

        return {"status": "success", "data": None, "raw": result}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "data": None, "raw": str(e)}


def display_result(experiment_name, result):
    """Pretty-print experiment results."""
    if result["status"] == "error":
        print(f"  FAILED: {result['raw']}")
        return

    if result["data"] is None:
        print(result["raw"])
        return

    data = result["data"]

    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            print(f"\n  --- Option {i} ---")
            if isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, str) and len(v) > 100:
                        print(f"  {k}: {v[:100]}...")
                    else:
                        print(f"  {k}: {v}")
            else:
                print(f"  {item}")
    elif isinstance(data, dict):
        print(json.dumps(data, indent=2))


def save_results(all_results):
    """Save all experiment results to a JSON file."""
    output_path = "/Users/jv222/Documents/Projects/Auto Research/experiment_output.json"
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading Twitter data...")
    posts = load_twitter_data()
    print(f"Loaded {len(posts)} posts")

    print("\nBuilding profile...")
    profile = build_profile(posts)

    print("\nWhich experiments to run?")
    for i, exp in enumerate(EXPERIMENTS):
        print(f"  {i+1}. {exp['name']} — {exp['description']}")
    print(f"  {len(EXPERIMENTS)+1}. ALL experiments")

    choice = input("\nEnter numbers (comma-separated) or 'all': ").strip().lower()

    if choice == 'all' or choice == str(len(EXPERIMENTS)+1):
        to_run = EXPERIMENTS
    else:
        indices = [int(x.strip())-1 for x in choice.split(',') if x.strip().isdigit()]
        to_run = [EXPERIMENTS[i] for i in indices if 0 <= i < len(EXPERIMENTS)]

    if not to_run:
        print("No experiments selected.")
        return

    all_results = {}
    for exp in to_run:
        t0 = time.time()
        result = run_experiment(exp, profile)
        dt = time.time() - t0
        display_result(exp['name'], result)
        all_results[exp['name']] = {
            "description": exp['description'],
            "result": result["raw"] if result["data"] is None else result["data"],
            "time_seconds": round(dt, 1),
        }
        print(f"\n  (completed in {dt:.1f}s)")

    save_results(all_results)

    print("\n" + "="*60)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*60)
    print(f"Results saved to experiment_output.json")
    print("Review the output and pick the best tweets to post!")


if __name__ == "__main__":
    main()
