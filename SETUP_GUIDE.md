# AutoResearch Setup Guide & Twitter Content Experiment Results

*By Jyothi (@jyothiwrites) — March 12, 2026*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Google Colab Setup (Step by Step)](#2-google-colab-setup)
3. [Anthropic Console Setup (Claude API)](#3-anthropic-console-setup)
4. [AutoResearch: LLM Training Experiments](#4-autoresearch-llm-training-experiments)
5. [Twitter Content Experiments](#5-twitter-content-experiments)
6. [Twitter Data Analysis Results](#6-twitter-data-analysis-results)
7. [Experiment Results: Generated Content](#7-experiment-results)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Project Overview

This project has two parts:

**Part A — Karpathy's AutoResearch (Google Colab)**
An autonomous AI experiment system that trains GPT language models. AI agents modify training code, run 5-minute experiments, evaluate results, and iterate — all without human intervention. Originally from [github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch).

**Part B — Twitter Content Experiments (Local)**
An autoresearch-inspired experiment loop that analyzes your Twitter/X data and uses Claude to generate optimized content for growing followers and impressions.

---

## 2. Google Colab Setup

### Step 1: Open Google Colab
- Go to [colab.research.google.com](https://colab.research.google.com)
- Sign in with your Google account

### Step 2: Upload the Notebook
- Click **File > Upload notebook**
- Select `autoresearch_colab.ipynb` from your local machine
- **OR** open from GitHub: **File > Open notebook > GitHub tab** > search `jyothivenkat-hub/autoresearch` > click `autoresearch_colab.ipynb`

### Step 3: Select GPU Runtime
1. Click **Runtime** in the top menu bar (between "Insert" and "Tools")
2. Click **Change runtime type**
3. A dialog box appears with:
   - **Runtime type**: Python 3 (default)
   - **Hardware accelerator**: Select **A100 GPU** (best) or **H100 GPU**
   - If those aren't available, **T4 GPU** works with reduced batch size
4. Click **Save**

> **Note**: If you see "Want access to premium GPUs? Purchase additional compute units" — you need Colab Pro or pay-as-you-go credits for A100/H100. T4 is free but less powerful.

> **Note**: If Colab says "The selected GPU type was not available. You are now connected to a T4" — the GPU you chose is busy. Try disconnecting and reconnecting, or try during off-peak hours.

### Step 4: Run the Setup Cells

Run each cell by clicking the **play button** (triangle icon) on the left of each cell, or use **Runtime > Run all**.

The cells do the following in order:

| Cell | What it does |
|------|-------------|
| 1. Verify GPU | Confirms which GPU you got |
| 2. Mount Google Drive | Persists data between Colab sessions |
| 3. Clone repo | Downloads autoresearch from GitHub |
| 4. Install uv | Installs the `uv` Python package manager |
| 5. Install dependencies | Installs PyTorch, tiktoken, etc. |
| 6. Symlink cache | Links data cache to Google Drive so you don't re-download |
| 7. Prepare data | Downloads training shards + trains BPE tokenizer (~2 min) |
| 8. Fix batch size | Reduces DEVICE_BATCH_SIZE from 128 to 32 for T4/A100-40GB |
| 9. Run baseline | Trains the model for 5 minutes and prints results |

### Step 5: Adding New Cells in Colab
- **Hover your mouse** between two existing cells — a thin line appears with **+ Code** and **+ Text** buttons
- Click **+ Code** to add a new code cell
- Type or paste code, then click the **play button** to run
- Alternatively, click **+ Code** in the top-left toolbar to add a cell at the bottom

### Step 6: Saving to GitHub from Colab
Add a cell with:
```python
!git add -A && git commit -m "experiment results" && git push
```

### Baseline Results (T4 GPU)

```
val_bpb:          1.089057
training_seconds: 300.5
total_seconds:    395.3
peak_vram_mb:     11702.0
mfu_percent:      14.88
total_tokens_M:   190.3
num_steps:        363
num_params_M:     50.3
depth:            8
```

---

## 3. Anthropic Console Setup

The Twitter experiments use the Claude API. Here's how to set it up:

### Step 1: Create an Anthropic Account
- Go to [console.anthropic.com](https://console.anthropic.com)
- Click **Sign up** (or log in if you already have an account)
- Verify your email

### Step 2: Add Credits
- Click **Billing** in the left sidebar
- Add a payment method
- Purchase credits (experiments cost ~$0.01-0.05 each with Claude Sonnet)

### Step 3: Create an API Key
1. Click **API Keys** in the left sidebar
2. Click **Create Key**
3. Give it a name (e.g., "twitter-experiments")
4. Copy the key — it starts with `sk-ant-...`
5. **Important**: Save this key securely. You won't be able to see it again.

### Step 4: Store the Key Locally
Create a `.env` file in your project directory:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> **Security**: The `.env` file is in `.gitignore` so it won't be pushed to GitHub. Never share your API key publicly.

### Step 5: Install Dependencies
```bash
pip3 install anthropic python-dotenv pandas numpy
```

### Step 6: Verify It Works
```python
python3 -c "
from dotenv import load_dotenv
import anthropic
load_dotenv()
client = anthropic.Anthropic()
resp = client.messages.create(model='claude-sonnet-4-20250514', max_tokens=20, messages=[{'role':'user','content':'Say OK'}])
print(resp.content[0].text)
"
```
Should print: `OK`

---

## 4. AutoResearch: LLM Training Experiments

### What AutoResearch Does
- Trains a 50M parameter GPT model on text data
- Fixed 5-minute training budget per experiment
- Metric: **val_bpb** (validation bits per byte) — lower is better
- You modify `train.py` to try different architectures, hyperparameters, etc.

### How to Run an Experiment on Colab

**Step 1**: Edit `train.py` with a `sed` command:
```python
!sed -i 's/^DEPTH = 8/DEPTH = 12/' /content/autoresearch/train.py
```

**Step 2**: Run the experiment:
```python
run_experiment('increase depth from 8 to 12')
```

The `run_experiment()` helper automatically:
- Commits your changes
- Runs 5-min training
- Parses results
- Keeps if val_bpb improved, reverts if not
- Logs to `results.tsv`

### Experiment Ideas

| Category | What to Change | Example |
|----------|---------------|---------|
| **Model depth** | `DEPTH = 8` → 12, 16 | More layers |
| **Model width** | `ASPECT_RATIO = 64` → 96, 128 | Wider layers |
| **Learning rate** | `MATRIX_LR = 0.04` → 0.06, 0.08 | Faster/slower learning |
| **Weight decay** | `WEIGHT_DECAY = 0.2` → 0.1, 0.0 | Regularization |
| **Batch size** | `DEVICE_BATCH_SIZE = 32` → 64 | If VRAM allows |
| **Activation** | `F.relu(x).square()` → `F.gelu(x)` | Different nonlinearity |
| **Window pattern** | `"SSSL"` → `"SSLL"`, `"LLLL"` | Attention window |
| **Warmup** | `WARMUP_RATIO = 0.0` → 0.1 | LR schedule |
| **Adam betas** | `(0.8, 0.95)` → `(0.9, 0.99)` | Optimizer momentum |

---

## 5. Twitter Content Experiments

### Data Source
- Exported from X Analytics: **Posts** tab > **Export data**
- File: `account_analytics_content_2026-02-14_2026-03-13.csv`
- 528 posts over ~2 weeks
- Columns: Post text, Impressions, Likes, Engagements, Bookmarks, Shares, New follows, Replies, Reposts, Profile visits

### How to Run Twitter Experiments
```bash
cd /Users/jv222/Documents/Projects/Auto\ Research
python3 twitter_experiments.py
```

Select which experiments to run (1-7 or "all"). Each takes ~15-30 seconds.

### Available Experiments

| # | Experiment | What It Does |
|---|-----------|-------------|
| 1 | **Original Post Topics** | Generates 5 optimized tweet ideas based on your data patterns |
| 2 | **Reply Strategies** | Templates for replying to @karpathy, @sundarpichai, @elonmusk, etc. |
| 3 | **Engagement Hooks** | 5 hook styles for the same topic (question, number, contrarian, story, milestone) |
| 4 | **Time & Format** | Full 7-day posting schedule with optimal times and themes |
| 5 | **A/B Test Posts** | Improved variations of your top 3 posts |
| 6 | **Follower Conversion** | 10 tweets specifically designed for follower growth |
| 7 | **Viral Reply Formulas** | 10 reusable reply templates for any big account |

---

## 6. Twitter Data Analysis Results

### Post Type Breakdown

| Type | Count | Avg Impressions | Avg Likes | Avg Follows |
|------|-------|----------------|-----------|-------------|
| Original | 85 | 148 | 2.5 | 0.07 |
| Reply | 443 | 215 | 1.3 | 0.06 |

**Key insight**: Replies get more impressions than original posts on average.

### Day of Week Performance

| Day | Posts | Avg Impressions | Avg Likes | Avg Follows |
|-----|-------|----------------|-----------|-------------|
| Monday | 77 | 147 | 0.9 | 0.0 |
| Tuesday | 83 | 249 | 1.7 | 0.1 |
| Wednesday | 100 | 102 | 1.3 | 0.2 |
| **Thursday** | **99** | **419** | **1.5** | **0.0** |
| Friday | 50 | 148 | 1.7 | 0.1 |
| Saturday | 53 | 163 | 1.3 | 0.0 |
| Sunday | 61 | 137 | 1.1 | 0.0 |

**Key insight**: Thursday has 2-3x more impressions than other days.

### Feature Impact

| Feature | With | Without | Multiplier |
|---------|------|---------|-----------|
| Emojis | 304 avg imp | 179 avg imp | 1.7x |
| Links | 497 avg imp | 166 avg imp | 3.0x |
| Numbers | 381 avg imp | 112 avg imp | 3.4x |
| Questions | 375 avg imp | 171 avg imp | 2.2x |
| Notable mentions | 346 avg imp | 202 avg imp | 1.7x |

### Text Length Performance

| Length | Count | Avg Impressions |
|--------|-------|----------------|
| < 50 chars | 130 | 75 |
| 50-100 chars | 125 | 270 |
| 100-150 chars | 98 | 260 |
| 150-200 chars | 60 | 202 |
| 200-280 chars | 65 | 186 |
| 280+ chars | 50 | 296 |

**Sweet spot**: 50-150 characters, with 280+ also performing well.

### Top 5 Posts by Impressions

1. **18,002 imp** — "@daniel_nguyenx 69 mins? Hey learnt to say no!! The people pleasing era is over." [reply]
2. **8,974 imp** — "@james406 Time to clear its memory, its a reflection of you. Mines still playful" [reply]
3. **4,457 imp** — "@minchoi This is wonderful, much needed. I can't access it yet" [reply]
4. **3,639 imp** — "@GeminiApp Tested it. Its so good" [reply]
5. **2,002 imp** — "@karpathy Bigger IDE? how about Star Wars level: holographic agent command centers" [reply]

### Top 5 Posts by Followers Gained

1. **7 follows** — "@trikcode Hey" [reply]
2. **5 follows** — "Just hit 100 followers!" [original]
3. **2 follows** — "@Venkydotdev @X Hey Venky, from another venky" [reply]
4. **2 follows** — "@jehniiee Hello" [reply]
5. **2 follows** — "@Zexyooo Hey Jyothi here, I am a researcher and AI builder" [reply]

---

## 7. Experiment Results

### Experiment 1: Original Post Topics

5 AI-focused tweet ideas optimized for your data patterns:

| # | Tweet | Target Metric | Confidence |
|---|-------|--------------|------------|
| 1 | "Just spent 3 hours debugging AI code... turns out I forgot to update my API key. Anyone else having those 'it's not the AI, it's me' moments?" | Impressions | High |
| 2 | "Hey AI builders! Drop a robot emoji if you're working on something cool this weekend. Let's connect and share what we're building!" | Follows | High |
| 3 | "ChatGPT just roasted my code harder than my coffee. Said my functions were 'overly complex' - I mean, it's not wrong" | Engagement | Medium |
| 4 | "200 followers! Thank you amazing humans! Every reply and like means the world. Here's to building cool AI stuff together!" | Engagement | High |
| 5 | "Plot twist: AI tools are making me a better researcher by forcing me to ask better questions. Anyone else finding this?" | Impressions | Medium |

### Experiment 2: Reply Strategies

Templates for replying to big accounts:

**@karpathy**
- AI topic: "This reminds me of {specific detail} - I've been experimenting with similar concepts and found {insight}. The implications for {application} could be huge!"
- Launch: "Just tested this and the {feature} is brilliant! The way it handles {technical aspect} is exactly what I needed for my AI experiments."
- Tips: Reply within first 30 mins, reference technical details, share building experience

**@sundarpichai**
- AI topic: "The potential for {use case} is incredible! I'm already seeing how this could transform {concrete example}. The accessibility angle is what excites me most."
- Launch: "Been waiting for this! Just tried it and the {feature} works flawlessly. As someone building AI tools, this changes everything for {workflow}."
- Tips: Focus on real-world impact, mention how it helps your process, reply quickly

**@elonmusk**
- AI topic: "Grok's approach to {topic} is fascinating! The creative outputs I'm getting are unlike anything else."
- Launch: "This is insane! Just spent hours playing with {feature} and the results are mind-blowing."
- Tips: Match energetic tone, use emojis, be genuinely excited, mention specific features

**@gregisenberg**
- AI topic: "This AI trend is perfect for solo builders! I'm seeing huge opportunities in {niche}."
- Launch: "Love this approach! The {strategy} is exactly what I needed to hear. Building in public with AI tools has been my focus."
- Tips: Connect to solo building/entrepreneurship, mention your journey

**@AravSrinivas**
- AI topic: "The search + reasoning combination is brilliant! I've been testing similar workflows and the accuracy improvement is remarkable."
- Launch: "Just tried this and wow! The way it handles {feature} is exactly what research workflows needed."
- Tips: Focus on search/research applications, ask thoughtful technical questions

### Experiment 3: Engagement Hooks

5 variations of "Building AI tools and shipping them publicly":

| Style | Tweet | Optimizes |
|-------|-------|-----------|
| **Question** | "Have you ever built an AI tool that nobody uses? I'm shipping my 3rd tool publicly this week and finally learning what people actually want vs what I think they need." | Engagement |
| **Number** | "3 things I learned shipping AI tools publicly: 1. Your first idea will suck (ship it anyway) 2. Users want simple, not sophisticated 3. Building alone = building blind" | Impressions |
| **Contrarian** | "Everyone says 'build in public' but most AI builders are still shipping in stealth. I've been documenting every failure, pivot, and breakthrough for 2 weeks." | Impressions |
| **Story** | "I just realized I've been building AI tools backwards. Spent weeks perfecting features -> crickets. Built a simple prototype in public -> 50 signups in 2 days" | Engagement |
| **Milestone** | "Just shipped my 5th AI tool publicly! 4 failed experiments -> 1 breakthrough. Each 'failure' taught me something the winner needed." | Follows |

### Experiment 4: Weekly Posting Plan

| Day | Originals | Replies | Themes | Strategy |
|-----|-----------|---------|--------|----------|
| **Monday** | 3 | 12 | Weekend AI discoveries, Monday motivation | Catch up on weekend conversations, reply to morning updates |
| **Tuesday** | 4 | 14 | Build in public, AI tool comparisons | Share progress, reply to researchers and builders |
| **Wednesday** | 5 | 13 | Tech commentary, AI predictions | Opinionated takes, engage with trending discussions |
| **Thursday** | 6 | 16 | Major announcements, milestones | PEAK DAY — most important content, heavy replies to big accounts |
| **Friday** | 4 | 14 | Week wrap-up, fun experiments | Share learnings, playful AI content, community building |
| **Saturday** | 2 | 8 | Weekend projects, casual discussions | Lower volume, quality over quantity |
| **Sunday** | 3 | 10 | Week ahead prep, reflections | Light engagement, setting up Monday conversations |

**Optimal posting times:**
- Morning: 7-9 AM PT (when big tech accounts post)
- Lunch: 12-1 PM PT (engagement peak)
- Evening: 5-7 PM PT (end of workday discussions)

### Experiment 5: A/B Test Variations

**Post 1** (18,002 impressions original):
> Original: "@daniel_nguyenx 69 mins? Hey learnt to say no!! The people pleasing era is over."

| Variation | Text | Prediction |
|-----------|------|-----------|
| A (hook) | "Wait... 69 MINUTES?! The people pleasing era is officially DEAD." | **Winner** — shock value + ALL CAPS |
| B (shorter) | "69 mins? Say no era activated" | Punchier but less engaging |
| C (CTA) | Original + "What's your longest people-pleasing story?" | Drives replies |

**Post 2** (8,974 impressions original):
> Original: "@james406 Time to clear its memory, its a reflection of you. Mines still playful"

| Variation | Text | Prediction |
|-----------|------|-----------|
| A (hook) | "Plot twist: Your AI's personality = YOUR personality. Time to clear its memory." | **Winner** — stronger hook |
| B (shorter) | "Clear its memory = clear yours. Mine's playful" | Concise but less impact |
| C (CTA) | Original + "Who else talks to their AI like a therapist?" | Drives engagement |

**Post 3** (4,457 impressions, 0 likes original):
> Original: "@minchoi This is wonderful, much needed. I can't access it yet, maybe still rolling out to all!"

| Variation | Text | Prediction |
|-----------|------|-----------|
| A (hook) | "This looks INCREDIBLE! Can't access it yet - anyone else waiting?" | More energetic |
| B (shorter) | "Wonderful! Can't access yet" | Too brief |
| C (CTA) | Original + "Drop a wave if you're also waiting!" | **Winner** — converts impressions to engagement |

### Experiment 6: Follower Conversion Posts

10 tweets optimized specifically for follower growth:

| # | Strategy | Tweet |
|---|----------|-------|
| 1 | Personal intro + value prop | "Hey! I'm Jyothi. AI researcher & builder sharing my journey in public. Just 2 weeks in and learning so much! Follow along for daily AI tool discoveries, honest takes, and building wins/fails" |
| 2 | Community building | "Who else is building AI tools as a solo creator? I'm documenting everything - the messy first attempts, breakthrough moments, and tools that actually work. Let's connect!" |
| 3 | Vulnerability + social proof | "Honestly, I joined Twitter 2 weeks ago not knowing what to expect. Now at 100+ followers sharing AI discoveries daily! If you're curious about cutting-edge tools - let's connect!" |
| 4 | Unique value prop | "Hey builders! I test 5+ AI tools weekly and share the gems (and duds) here. No fluff, just real experiences. Follow for honest reviews you won't find elsewhere!" |
| 5 | Personality + authenticity | "Plot twist: The people-pleasing era is over. Now I'm building AI tools, sharing honest opinions, and connecting with amazing creators! I'm Jyothi - researcher turned builder." |
| 6 | Social proof + gratitude | "Just hit 100k impressions in 2 weeks! Wild! Thank you to everyone who engages with my AI tool reviews. If you're not following yet - I share daily discoveries and honest takes!" |
| 7 | Service positioning | "Hey fellow AI enthusiasts! I'm the person testing tools so you don't have to. From Gemini's latest features to Grok's creative capabilities - I share real user experiences." |
| 8 | Expertise positioning | "Who else thinks AI conversations are getting sassier? I'm Jyothi - I study these interactions daily and share fascinating finds! From Claude's helpfulness to ChatGPT's quirks." |
| 9 | Vulnerability + personal story | "Confession: I built my first AI tool for an audience of 1... me. Now sharing everything I learn publicly! Hey, I'm Jyothi. Follow along for honest build stories and tool discoveries." |
| 10 | Impressive stats | "Hey Twitter! 2 weeks, 500+ posts, countless AI tools tested! I'm sharing this wild journey of building in public. Follow for daily AI discoveries and real builder insights!" |

### Experiment 7: Viral Reply Formulas

10 reusable reply templates for any big account's post:

**Humor/Wit:**

| Template | Example |
|----------|---------|
| "[TIME/NUMBER]? [RELATABLE REACTION]! The [OPPOSITE BEHAVIOR] era is over." | "40 hours coding? Time to touch grass! The basement dweller era is over." |
| "Plot twist: [UNEXPECTED BUT LOGICAL SCENARIO]" | "Plot twist: the AI is actually three interns in a trenchcoat taking turns at ChatGPT" |
| "Me: [INTERNAL THOUGHT] Also me: [CONTRADICTORY ACTION]. Anyone else or just me?" | "Me: 'I need better work-life balance' Also me: *codes at 2am because I had a cool idea*. Anyone else?" |

**Adding Unique Insight:**

| Template | Example |
|----------|---------|
| "This reminds me of [HISTORICAL PARALLEL]. Same energy as [SPECIFIC EXAMPLE] - [BRIEF INSIGHT]." | "This reminds me of the printing press disruption. Same energy as scribes panicking in 1440." |
| "The real kicker: [DEEPER IMPLICATION]. This isn't just about [SURFACE] - it's about [BIGGER PICTURE]." | "The real kicker: we're not just automating tasks, we're changing what 'intelligence' means." |

**Personal Story:**

| Template | Example |
|----------|---------|
| "Been there! [BRIEF EXPERIENCE]. Now I [LESSON]. [CONCLUSION]." | "Been there! Spent 3 months perfecting a feature nobody used. Now I ship fast and iterate." |
| "[NUMBER] [TIME] ago, I thought [OLD BELIEF]. Today [CURRENT REALITY]. Wild how [CHANGE] happens!" | "2 years ago, I thought AI would never understand context. Today it's writing my emails better than I do." |

**Contrarian but Respectful:**

| Template | Example |
|----------|---------|
| "Hot take: [OPPOSITE PERSPECTIVE], but [ACKNOWLEDGMENT]. Maybe we need both approaches?" | "Hot take: failure isn't always a teacher. Maybe we need both approaches?" |
| "Unpopular opinion: [THOUGHTFUL TAKE]. Not saying [ORIGINAL VIEW] is wrong, but [NUANCE]." | "Unpopular opinion: maybe we're solving the wrong problems with AI." |

**Smart Follow-up Question:**

| Template | Example |
|----------|---------|
| "This is fascinating! What happens when [NEXT SCENARIO]? Could this lead to [IMPLICATION]?" | "What happens when everyone has access to this? Could this lead to a new kind of digital divide?" |

---

## 8. Troubleshooting

### Google Colab Issues

| Problem | Solution |
|---------|----------|
| "GPU not available" | Disconnect and reconnect, or try off-peak hours |
| OOM (Out of Memory) on T4 | Reduce `DEVICE_BATCH_SIZE` to 16 or 32 |
| Flash Attention error on T4 | T4 doesn't support FA3 — need A100+ for autoresearch |
| "bfloat16 not supported" warning | Normal on T4, training may still work |
| Colab disconnects | Mount Google Drive to persist data |

### Claude API Issues

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Check `.env` file, ensure no extra spaces |
| Rate limited | Wait 60 seconds and retry |
| "Insufficient credits" | Add credits at console.anthropic.com > Billing |

### File Locations

| File | Purpose |
|------|---------|
| `autoresearch_colab.ipynb` | Google Colab notebook for LLM experiments |
| `twitter_analysis.py` | Analyzes Twitter CSV data for patterns |
| `twitter_experiments.py` | Runs content experiments using Claude API |
| `experiment_output.json` | Full experiment results (machine-readable) |
| `.env` | API key storage (not committed to git) |
| `train.py` | GPT training script (modified by experiments) |
| `prepare.py` | Data prep (read-only, do not modify) |
| `program.md` | Instructions for autonomous AI agents |

---

*Generated with Claude Code — github.com/jyothivenkat-hub/autoresearch*
