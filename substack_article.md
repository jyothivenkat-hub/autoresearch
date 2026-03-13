# I Used Karpathy's AutoResearch to Optimize My Twitter Growth — Step by Step

*A beginner-friendly walkthrough of setting up AI-powered experiments on Google Colab, analyzing 528 tweets, and finding what actually drives followers and impressions.*

---

Last week, Andrej Karpathy released [AutoResearch](https://github.com/karpathy/autoresearch) — a system where AI agents autonomously run machine learning experiments overnight while you sleep.

I set it up. I broke it. I fixed it. Then I thought: what if I used the same experimental approach on my own Twitter data?

This post walks through everything I did, step by step.

---

## What is AutoResearch?

AutoResearch is a loop:

1. AI agent reads the training code
2. Makes a change (e.g., "increase model depth")
3. Trains a neural network for exactly 5 minutes
4. Checks the score — did it improve?
5. If yes, keep the change. If no, revert.
6. Repeat.

You start it before bed. Wake up to 100 completed experiments.

The project has three files:
- **prepare.py** — downloads data, builds a tokenizer (read-only, don't touch)
- **train.py** — the training script (this is what the AI modifies)
- **program.md** — instructions that tell the AI how to run experiments

Simple and elegant. But there's a catch: it needs an NVIDIA GPU.

---

## Step 1: Set Up Google Colab

I don't have an NVIDIA GPU. I'm on a MacBook. So I used Google Colab — Google's free cloud notebook environment that gives you access to GPUs.

Here's how:

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Sign in with your Google account
3. Click **File > Upload notebook** (or create a new one)

### Select a GPU

4. Click **Runtime** in the top menu bar
5. Click **Change runtime type**
6. Under **Hardware accelerator**, select **A100 GPU** (best option)
7. Click **Save**

If Colab says the GPU isn't available, it'll give you a T4 instead. That's fine — it works, just needs a small adjustment (more on that below).

---

## Step 2: Install AutoResearch on Colab

In your Colab notebook, run these cells one at a time:

**Cell 1: Verify your GPU**
```python
!nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
```

**Cell 2: Clone the repo**
```python
!git clone https://github.com/karpathy/autoresearch.git /content/autoresearch
%cd /content/autoresearch
```

**Cell 3: Install the package manager**
```python
!curl -LsSf https://astral.sh/uv/install.sh | sh
import os
os.environ['PATH'] = os.path.expanduser('~/.local/bin') + ':' + os.environ['PATH']
```

**Cell 4: Install dependencies**
```python
!uv sync
```

**Cell 5: Download training data (~2 minutes)**
```python
!uv run prepare.py
```

---

## Step 3: Fix the Batch Size (If You Got a T4)

The default batch size of 128 is too large for the T4's memory. You'll get an `Out of Memory` error.

The fix is one line:

```python
!sed -i 's/DEVICE_BATCH_SIZE = 128/DEVICE_BATCH_SIZE = 32/' /content/autoresearch/train.py
```

This reduces the per-step batch from 128 to 32. The system automatically compensates by doing more gradient accumulation steps, so the effective training stays the same — just a bit slower.

---

## Step 4: Run the Baseline

```python
!uv run train.py
```

This trains a 50-million parameter GPT model for 5 minutes. When it finishes, you'll see:

```
val_bpb:          1.089057
training_seconds: 300.5
peak_vram_mb:     11702.0
```

That **val_bpb of 1.089** is the baseline. Lower is better. Every experiment tries to beat this number.

---

## Step 5: Run Experiments

Now the fun part. Each experiment follows the same pattern:

1. Change something in `train.py`
2. Run training for 5 minutes
3. Check if `val_bpb` improved
4. Keep or revert

**Example — increase model depth:**
```python
!sed -i 's/^DEPTH = 8/DEPTH = 12/' /content/autoresearch/train.py
!uv run train.py
```

**Other things to try:**

| What to Change | Command |
|---------------|---------|
| More layers | `sed -i 's/DEPTH = 8/DEPTH = 12/'` |
| Wider model | `sed -i 's/ASPECT_RATIO = 64/ASPECT_RATIO = 96/'` |
| Higher learning rate | `sed -i 's/MATRIX_LR = 0.04/MATRIX_LR = 0.08/'` |
| Less weight decay | `sed -i 's/WEIGHT_DECAY = 0.2/WEIGHT_DECAY = 0.1/'` |
| Different activation | Replace `F.relu(x).square()` with `F.gelu(x)` in train.py |

Each experiment takes ~5 minutes. You can run 12 per hour, about 100 overnight.

---

## The Pivot: What About Twitter?

AutoResearch optimizes neural networks. But the pattern — **measure, experiment, keep what works** — applies to anything measurable.

I had 2 weeks of Twitter data. 528 posts. Every one tracked with impressions, likes, follows, and engagements.

What if I ran the same loop, but optimized for followers and impressions instead of a loss function?

---

## Step 6: Get Your Twitter Data

1. Go to [analytics.x.com](https://analytics.x.com)
2. Click the **Posts** tab
3. Click **Export data** (top right)
4. Download the CSV

You'll get a file with columns like: Post text, Impressions, Likes, Engagements, New follows, Replies, Reposts.

---

## Step 7: Set Up the Claude API

The Twitter experiments use Claude to analyze your data and generate optimized content.

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and verify your email
3. Click **Billing** in the left sidebar and add a payment method
4. Click **API Keys** in the left sidebar
5. Click **Create Key**
6. Copy the key (starts with `sk-ant-...`)

Store it in a `.env` file in your project:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Install the dependencies:
```bash
pip3 install anthropic python-dotenv pandas numpy
```

Total cost for all 7 experiments: less than $0.50.

---

## Step 8: Analyze Your Twitter Data

Before running experiments, I needed to understand what was already working. I wrote a script to crunch all 528 posts.

The results surprised me.

### Finding 1: Replies beat original posts

| Post Type | Count | Avg Impressions |
|-----------|-------|----------------|
| Original posts | 85 | 148 |
| Replies | 443 | 215 |

I was spending energy crafting original tweets when my replies were getting **45% more impressions**. My top post? A reply with 18,002 impressions. My best original? 1,138.

### Finding 2: Numbers are a 3.4x multiplier

| Feature | Avg Impressions |
|---------|----------------|
| With numbers | 381 |
| Without numbers | 112 |

"Just spent 3 hours debugging" beats "Spent a while debugging" every time.

### Finding 3: Emojis boost impressions 1.7x

| Feature | Avg Impressions |
|---------|----------------|
| With emojis | 304 |
| Without emojis | 179 |

### Finding 4: Thursday is 3x better than other days

| Day | Avg Impressions |
|-----|----------------|
| Thursday | 419 |
| Tuesday | 249 |
| Saturday | 163 |
| Monday | 147 |
| Sunday | 137 |

### Finding 5: Personal greetings drive followers

My top follower-gaining post was literally just **"@trikcode Hey"** — 7 new followers from two words and a wave emoji.

The second best? **"Just hit 100 followers!"** — 5 follows.

People don't follow hot takes. They follow humans who make them feel seen.

---

## Step 9: Run the Twitter Experiments

I built 7 experiments that feed my Twitter analysis into Claude and generate optimized content.

```bash
python3 twitter_experiments.py
```

Select "all" to run everything. Each experiment takes 15-30 seconds.

Here's what each one found:

---

### Experiment 1: Original Post Ideas

Claude combined my winning patterns (numbers + emojis + conversational tone + questions) into ready-to-post tweets:

> "Just spent 3 hours debugging AI code... turns out I forgot to update my API key. Anyone else having those 'it's not the AI, it's me' moments?"

Every element maps to a pattern that performed well in my data.

---

### Experiment 2: Reply Strategies for Big Accounts

Replying to @karpathy, @sundarpichai, and @elonmusk drives massive impressions. But not all replies are equal.

**Bad reply:** "Great post!"

**Good reply:** "Just tested this and the [specific feature] is brilliant! The way it handles [technical aspect] is exactly what I needed for my AI experiments."

The formula: **Specific detail + Personal experience + Follow-up question**

Key insight: **reply within 30 minutes.** Early replies get surfaced to the poster's entire audience.

---

### Experiment 3: Five Hook Styles, Same Topic

I tested 5 different openings for the same topic ("building AI tools in public"):

| Hook Style | Opening Line | Best For |
|------------|-------------|----------|
| Question | "Have you ever built an AI tool that nobody uses?" | Engagement |
| Number | "3 things I learned shipping AI tools publicly..." | Impressions |
| Contrarian | "Everyone says 'build in public' but most builders ship in stealth" | Impressions |
| Story | "I just realized I've been building AI tools backwards..." | Engagement |
| Milestone | "Just shipped my 5th AI tool publicly!" | Followers |

Same content. Wildly different outcomes depending on how you open.

---

### Experiment 4: The Optimal Weekly Schedule

| Day | Original Posts | Replies | Strategy |
|-----|---------------|---------|----------|
| Monday | 3 | 12 | Catch up on weekend conversations |
| Tuesday | 4 | 14 | Share progress, reply to researchers |
| Wednesday | 5 | 13 | Opinionated takes on trending topics |
| **Thursday** | **6** | **16** | **Peak day — save your best content** |
| Friday | 4 | 14 | Week wrap-up, playful content |
| Saturday | 2 | 8 | Low volume, quality over quantity |
| Sunday | 3 | 10 | Light engagement, prep for Monday |

**Best times to post:** 7-9 AM PT, 12-1 PM PT, 5-7 PM PT.

---

### Experiment 5: A/B Testing My Best Posts

I took my top reply (18,002 impressions) and generated three variations:

**Original:** "@daniel_nguyenx 69 mins? Hey learnt to say no!! The people pleasing era is over."

| Variation | Text | Prediction |
|-----------|------|-----------|
| A | "Wait... 69 MINUTES?! The people pleasing era is officially DEAD." | Wins on impressions (more shock value) |
| B | "69 mins? Say no era activated" | Punchier but less engaging |
| C | Original + "What's your longest people-pleasing story?" | Wins on engagement (invites replies) |

---

### Experiment 6: Follower Growth Posts

Followers come from **personal connection**, not clever content. The top generated post:

> "Confession: I built my first AI tool for an audience of 1... me. Now sharing everything I learn publicly! Hey, I'm Jyothi. Follow along for honest build stories and tool discoveries."

The formula: **Vulnerability + personal greeting + clear value proposition**

---

### Experiment 7: Viral Reply Templates

10 reusable templates that work on any big account's post. My favorite:

**Template:**
> "Me: [INTERNAL THOUGHT] Also me: [CONTRADICTORY ACTION]. Anyone else or just me?"

**Example:**
> "Me: 'I need better work-life balance.' Also me: *codes at 2am because I had a cool idea.* Anyone else or just me?"

Works because it's self-deprecating, relatable, and ends with a question.

---

## The Takeaway

Karpathy built AutoResearch for neural networks. But the real insight is the loop itself:

1. **Measure** what's already working
2. **Hypothesize** why
3. **Generate** variations
4. **Test** against reality
5. **Keep** improvements, **discard** the rest
6. **Repeat**

The difference between guessing and growing is data. I had 528 data points telling me exactly what my audience responds to. I just wasn't listening until I automated the analysis.

---

## What's Next

1. Run the posting plan for 2 weeks and compare to baseline
2. Build a daily content generator that suggests posts each morning
3. Automate the feedback loop — pull fresh analytics weekly, re-run experiments, adjust

I'll share the follow-up results.

---

## Try It Yourself

Everything is open source: [github.com/jyothivenkat-hub/autoresearch](https://github.com/jyothivenkat-hub/autoresearch)

What you need:
- A Google account (for Colab)
- Your Twitter/X analytics CSV (download from analytics.x.com > Posts > Export)
- A Claude API key from [console.anthropic.com](https://console.anthropic.com) (~$0.50 for all experiments)

---

*I share AI tools, experiments, and build-in-public updates on X [@jyothiwrites](https://x.com/jyothiwrites). Say hi — apparently that's my best growth strategy.*
