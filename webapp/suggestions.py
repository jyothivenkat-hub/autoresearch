"""Daily content suggestion engine."""

import json
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

MODEL = "claude-sonnet-4-20250514"


def generate_suggestions(profile_text, num_suggestions=5):
    """Generate daily posting suggestions based on profile analysis."""
    today = datetime.now().strftime('%A')

    prompt = f"""{profile_text}

---

Today is {today}. Generate {num_suggestions} tweet suggestions for today.

For each suggestion, consider:
- Day-of-week performance patterns from the data
- The content patterns that work best (numbers, emojis, questions, etc.)
- Mix of original posts and reply strategies
- Authentic voice matching the top posts

For each suggestion provide:
- The exact tweet text (ready to copy-paste)
- What strategy it uses
- Why it should work based on the data
- What metric it targets (impressions, follows, or engagement)

Format as JSON array:
[{{"tweet": "...", "strategy": "...", "reasoning": "...", "target_metric": "impressions|follows|engagement"}}]"""

    client = anthropic.Anthropic()
    t0 = time.time()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        result_text = response.content[0].text

        json_start = result_text.find('[')
        json_end = result_text.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            try:
                suggestions = json.loads(result_text[json_start:json_end])
                return {"status": "success", "suggestions": suggestions,
                        "time_seconds": round(time.time() - t0, 1)}
            except json.JSONDecodeError:
                pass

        return {"status": "success", "suggestions": [], "raw": result_text,
                "time_seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"status": "error", "message": str(e),
                "time_seconds": round(time.time() - t0, 1)}
