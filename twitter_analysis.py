"""
Twitter/X Post Analysis — Find patterns that drive impressions & followers.
Analyzes post-level data to identify what works.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv('/Users/jv222/Downloads/account_analytics_content_2026-02-14_2026-03-13.csv')

print(f"Total posts: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"Date range: {df['Date'].iloc[-1]} to {df['Date'].iloc[0]}")
print()

# Parse dates
df['parsed_date'] = pd.to_datetime(df['Date'], format='%a, %b %d, %Y')
df['day_of_week'] = df['parsed_date'].dt.day_name()

# Classify post type
def classify_post(text):
    text = str(text)
    if text.startswith('@'):
        return 'reply'
    elif 'RT @' in text:
        return 'retweet'
    else:
        return 'original'

df['post_type'] = df['Post text'].apply(classify_post)
df['text_length'] = df['Post text'].astype(str).str.len()
df['has_emoji'] = df['Post text'].astype(str).str.contains(r'[\U0001f600-\U0001f9ff\U00002700-\U000027bf\U0001f300-\U0001f5ff]', regex=True)
df['has_link'] = df['Post text'].astype(str).str.contains('http', case=False)
df['has_question'] = df['Post text'].astype(str).str.contains(r'\?', regex=True)
df['has_numbers'] = df['Post text'].astype(str).str.contains(r'\d+', regex=True)
df['word_count'] = df['Post text'].astype(str).str.split().str.len()

# Mentions of notable accounts
df['mentions_notable'] = df['Post text'].astype(str).str.contains(
    r'@(sundarpichai|kaborofficial|elonmusk|gregisenberg|andrewchen|AravSrinivas)', regex=True)

print("=" * 60)
print("1. POST TYPE BREAKDOWN")
print("=" * 60)
type_stats = df.groupby('post_type').agg(
    count=('Impressions', 'count'),
    avg_impressions=('Impressions', 'mean'),
    median_impressions=('Impressions', 'median'),
    avg_likes=('Likes', 'mean'),
    avg_follows=('New follows', 'mean'),
    avg_engagements=('Engagements', 'mean'),
).round(1)
print(type_stats)
print()

print("=" * 60)
print("2. TOP 15 POSTS BY IMPRESSIONS")
print("=" * 60)
top = df.nlargest(15, 'Impressions')[['Post text', 'Impressions', 'Likes', 'New follows', 'Engagements', 'post_type']]
for i, row in top.iterrows():
    text = str(row['Post text'])[:100]
    print(f"\n  {row['Impressions']:,} imp | {row['Likes']} likes | {row['New follows']} follows | [{row['post_type']}]")
    print(f"  \"{text}...\"" if len(str(row['Post text'])) > 100 else f"  \"{text}\"")
print()

print("=" * 60)
print("3. TOP 15 POSTS BY NEW FOLLOWERS")
print("=" * 60)
top_follows = df.nlargest(15, 'New follows')[['Post text', 'Impressions', 'Likes', 'New follows', 'post_type']]
for i, row in top_follows.iterrows():
    text = str(row['Post text'])[:100]
    print(f"\n  {row['New follows']} follows | {row['Impressions']:,} imp | {row['Likes']} likes | [{row['post_type']}]")
    print(f"  \"{text}...\"" if len(str(row['Post text'])) > 100 else f"  \"{text}\"")
print()

print("=" * 60)
print("4. DAY OF WEEK PERFORMANCE")
print("=" * 60)
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_stats = df.groupby('day_of_week').agg(
    posts=('Impressions', 'count'),
    avg_impressions=('Impressions', 'mean'),
    avg_likes=('Likes', 'mean'),
    avg_follows=('New follows', 'mean'),
).round(1).reindex(day_order)
print(day_stats)
print()

print("=" * 60)
print("5. TEXT LENGTH vs PERFORMANCE")
print("=" * 60)
df['length_bucket'] = pd.cut(df['text_length'], bins=[0, 50, 100, 150, 200, 280, 500],
                              labels=['<50', '50-100', '100-150', '150-200', '200-280', '280+'])
length_stats = df.groupby('length_bucket', observed=True).agg(
    count=('Impressions', 'count'),
    avg_impressions=('Impressions', 'mean'),
    avg_likes=('Likes', 'mean'),
    avg_follows=('New follows', 'mean'),
).round(1)
print(length_stats)
print()

print("=" * 60)
print("6. FEATURE ANALYSIS")
print("=" * 60)
for feature in ['has_emoji', 'has_link', 'has_question', 'has_numbers', 'mentions_notable']:
    yes = df[df[feature] == True]
    no = df[df[feature] == False]
    print(f"\n{feature}:")
    print(f"  YES ({len(yes)} posts): avg {yes['Impressions'].mean():.0f} imp, {yes['Likes'].mean():.1f} likes, {yes['New follows'].mean():.2f} follows")
    print(f"  NO  ({len(no)} posts): avg {no['Impressions'].mean():.0f} imp, {no['Likes'].mean():.1f} likes, {no['New follows'].mean():.2f} follows")
print()

print("=" * 60)
print("7. ENGAGEMENT RATE (engagements/impressions)")
print("=" * 60)
df['engagement_rate'] = (df['Engagements'] / df['Impressions'].replace(0, 1) * 100).round(2)
top_engagement = df[df['Impressions'] > 50].nlargest(10, 'engagement_rate')[
    ['Post text', 'engagement_rate', 'Impressions', 'Likes', 'post_type']]
for i, row in top_engagement.iterrows():
    text = str(row['Post text'])[:100]
    print(f"\n  {row['engagement_rate']}% rate | {row['Impressions']:,} imp | [{row['post_type']}]")
    print(f"  \"{text}...\"" if len(str(row['Post text'])) > 100 else f"  \"{text}\"")
print()

# Original posts only analysis
print("=" * 60)
print("8. ORIGINAL POSTS ONLY — WHAT WORKS")
print("=" * 60)
originals = df[df['post_type'] == 'original'].copy()
print(f"Total original posts: {len(originals)}")
print(f"Avg impressions: {originals['Impressions'].mean():.0f}")
print(f"Avg likes: {originals['Likes'].mean():.1f}")
print(f"Avg follows: {originals['New follows'].mean():.2f}")

# Correlation analysis for originals
print("\nCorrelation with Impressions (original posts):")
numeric_cols = ['text_length', 'word_count', 'has_emoji', 'has_link', 'has_question', 'has_numbers']
for col in numeric_cols:
    corr = originals[col].astype(float).corr(originals['Impressions'].astype(float))
    print(f"  {col:20s}: {corr:+.3f}")

print("\nCorrelation with New follows (original posts):")
for col in numeric_cols:
    corr = originals[col].astype(float).corr(originals['New follows'].astype(float))
    print(f"  {col:20s}: {corr:+.3f}")
