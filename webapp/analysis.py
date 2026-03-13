"""Twitter data analysis engine — returns structured results."""

import pandas as pd
import numpy as np


def classify_post(text):
    text = str(text)
    if text.startswith('@'):
        return 'reply'
    elif 'RT @' in text:
        return 'retweet'
    return 'original'


def compute_features(df):
    df = df.copy()
    df['post_type'] = df['Post text'].apply(classify_post)
    df['text_length'] = df['Post text'].astype(str).str.len()
    df['word_count'] = df['Post text'].astype(str).str.split().str.len()
    df['has_emoji'] = df['Post text'].astype(str).str.contains(
        r'[\U0001f600-\U0001f9ff\U00002700-\U000027bf\U0001f300-\U0001f5ff]', regex=True)
    df['has_link'] = df['Post text'].astype(str).str.contains('http', case=False)
    df['has_question'] = df['Post text'].astype(str).str.contains(r'\?', regex=True)
    df['has_numbers'] = df['Post text'].astype(str).str.contains(r'\d+', regex=True)
    try:
        df['parsed_date'] = pd.to_datetime(df['Date'], format='%a, %b %d, %Y')
        df['day_of_week'] = df['parsed_date'].dt.day_name()
    except Exception:
        df['day_of_week'] = 'Unknown'
    return df


def analyze_posts(posts_df):
    df = compute_features(posts_df)
    results = {}

    # Summary
    results['summary'] = {
        'total_posts': len(df),
        'total_impressions': int(df['Impressions'].sum()),
        'avg_impressions': round(df['Impressions'].mean(), 1),
        'total_likes': int(df['Likes'].sum()),
        'avg_likes': round(df['Likes'].mean(), 1),
        'total_follows': int(df['New follows'].sum()),
        'avg_follows': round(df['New follows'].mean(), 2),
    }

    # Post type breakdown
    type_stats = df.groupby('post_type').agg(
        count=('Impressions', 'count'),
        avg_impressions=('Impressions', 'mean'),
        avg_likes=('Likes', 'mean'),
        avg_follows=('New follows', 'mean'),
    ).round(1).to_dict('index')
    results['post_type_breakdown'] = type_stats

    # Top posts by impressions
    top_imp = df.nlargest(10, 'Impressions')
    results['top_by_impressions'] = top_imp[['Post text', 'Impressions', 'Likes',
        'New follows', 'Engagements', 'post_type']].to_dict('records')

    # Top posts by followers
    top_fol = df.nlargest(10, 'New follows')
    results['top_by_follows'] = top_fol[['Post text', 'Impressions', 'Likes',
        'New follows', 'post_type']].to_dict('records')

    # Day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if 'day_of_week' in df.columns and df['day_of_week'].iloc[0] != 'Unknown':
        day_stats = df.groupby('day_of_week').agg(
            posts=('Impressions', 'count'),
            avg_impressions=('Impressions', 'mean'),
            avg_likes=('Likes', 'mean'),
            avg_follows=('New follows', 'mean'),
        ).round(1)
        day_stats = day_stats.reindex([d for d in day_order if d in day_stats.index])
        results['day_of_week'] = day_stats.to_dict('index')
    else:
        results['day_of_week'] = {}

    # Feature analysis
    features = {}
    for feat in ['has_emoji', 'has_link', 'has_question', 'has_numbers']:
        yes = df[df[feat] == True]
        no = df[df[feat] == False]
        label = feat.replace('has_', '').title()
        features[label] = {
            'with': {
                'count': len(yes),
                'avg_impressions': round(yes['Impressions'].mean(), 0) if len(yes) > 0 else 0,
                'avg_likes': round(yes['Likes'].mean(), 1) if len(yes) > 0 else 0,
            },
            'without': {
                'count': len(no),
                'avg_impressions': round(no['Impressions'].mean(), 0) if len(no) > 0 else 0,
                'avg_likes': round(no['Likes'].mean(), 1) if len(no) > 0 else 0,
            },
        }
        if features[label]['without']['avg_impressions'] > 0:
            features[label]['multiplier'] = round(
                features[label]['with']['avg_impressions'] / features[label]['without']['avg_impressions'], 1)
        else:
            features[label]['multiplier'] = 0
    results['feature_analysis'] = features

    # Text length buckets
    df['length_bucket'] = pd.cut(df['text_length'], bins=[0, 50, 100, 150, 200, 280, 1000],
                                  labels=['<50', '50-100', '100-150', '150-200', '200-280', '280+'])
    length_stats = df.groupby('length_bucket', observed=True).agg(
        count=('Impressions', 'count'),
        avg_impressions=('Impressions', 'mean'),
    ).round(1).to_dict('index')
    results['text_length'] = length_stats

    return results


def build_profile(posts_df):
    """Build profile text for Claude prompts."""
    df = compute_features(posts_df)
    originals = df[df['post_type'] == 'original']
    replies = df[df['post_type'] == 'reply']
    top_imp = df.nlargest(10, 'Impressions')
    top_follows = df.nlargest(10, 'New follows')
    top_likes = df.nlargest(10, 'Likes')

    profile = f"""TWITTER PROFILE ANALYSIS
Total posts: {len(df)} ({len(originals)} original, {len(replies)} replies)

STATS:
- Originals avg {originals['Impressions'].mean():.0f} impressions
- Replies avg {replies['Impressions'].mean():.0f} impressions

TOP 10 BY IMPRESSIONS:
"""
    for _, p in top_imp.iterrows():
        text = str(p['Post text'])[:120]
        profile += f"- {p['Impressions']:,} imp | {p['Likes']} likes | {p['New follows']} follows | \"{text}\"\n"

    profile += "\nTOP 10 BY FOLLOWERS:\n"
    for _, p in top_follows.iterrows():
        text = str(p['Post text'])[:120]
        profile += f"- {p['New follows']} follows | {p['Impressions']:,} imp | \"{text}\"\n"

    profile += "\nTOP 10 BY LIKES:\n"
    for _, p in top_likes.iterrows():
        text = str(p['Post text'])[:120]
        profile += f"- {p['Likes']} likes | {p['Impressions']:,} imp | \"{text}\"\n"

    # Feature analysis
    for feat in ['has_emoji', 'has_link', 'has_question', 'has_numbers']:
        yes_avg = df[df[feat] == True]['Impressions'].mean()
        no_avg = df[df[feat] == False]['Impressions'].mean()
        label = feat.replace('has_', '')
        profile += f"\n{label}: {yes_avg:.0f} avg imp WITH vs {no_avg:.0f} WITHOUT"

    if 'day_of_week' in df.columns:
        best_day = df.groupby('day_of_week')['Impressions'].mean().idxmax()
        best_avg = df.groupby('day_of_week')['Impressions'].mean().max()
        profile += f"\n\nBest day: {best_day} ({best_avg:.0f} avg impressions)"

    return profile
