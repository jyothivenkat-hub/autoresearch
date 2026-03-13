"""Flask app for Twitter content optimizer."""

import os
import io
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
from dotenv import load_dotenv

from .models import (init_db, save_upload, save_posts, get_latest_upload,
                     get_posts, save_experiment, get_experiments,
                     save_suggestions, get_suggestions, mark_suggestion_used)
from .analysis import analyze_posts, build_profile, compute_features
from .experiments import get_experiment_list, run_experiment, run_custom_experiment
from .suggestions import generate_suggestions


COLUMN_RENAME = {
    'post_text': 'Post text', 'impressions': 'Impressions',
    'likes': 'Likes', 'engagements': 'Engagements',
    'new_follows': 'New follows', 'date': 'Date',
    'bookmarks': 'Bookmarks', 'shares': 'Shares',
    'replies': 'Replies', 'reposts': 'Reposts',
}


def posts_to_df(upload_id):
    """Load posts from DB and return a DataFrame with expected column names."""
    posts = get_posts(upload_id)
    df = pd.DataFrame(posts)
    if not df.empty:
        df = df.rename(columns=COLUMN_RENAME)
    return df


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    init_db()

    # --- Dashboard ---
    @app.route('/')
    def index():
        upload = get_latest_upload()
        if not upload:
            return redirect(url_for('upload'))
        df = posts_to_df(upload['id'])
        if df.empty:
            return redirect(url_for('upload'))
        analysis = analyze_posts(df)
        experiments = get_experiments(upload['id'])
        suggestions = get_suggestions(upload['id'], unused_only=True)
        return render_template('index.html', upload=upload, analysis=analysis,
                               experiments=experiments, suggestions=suggestions[:5])

    # --- Upload ---
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if request.method == 'POST':
            file = request.files.get('csv_file')
            if not file or not file.filename.endswith('.csv'):
                flash('Please upload a CSV file.')
                return redirect(url_for('upload'))

            content = file.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(content))

            required_cols = ['Post text', 'Impressions', 'Likes']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                flash(f'CSV is missing required columns: {", ".join(missing)}')
                return redirect(url_for('upload'))

            upload_id = save_upload(file.filename, len(df))
            save_posts(upload_id, df)
            flash(f'Uploaded {len(df)} posts successfully!')
            return redirect(url_for('analysis'))

        return render_template('upload.html')

    # --- Analysis ---
    @app.route('/analysis')
    def analysis():
        upload = get_latest_upload()
        if not upload:
            return redirect(url_for('upload'))
        df = posts_to_df(upload['id'])
        if df.empty:
            return redirect(url_for('upload'))
        results = analyze_posts(df)
        return render_template('analysis.html', analysis=results, upload=upload)

    # --- Experiments ---
    @app.route('/experiments')
    def experiments():
        upload = get_latest_upload()
        exp_list = get_experiment_list()
        past_experiments = get_experiments(upload['id']) if upload else []
        return render_template('experiments.html', experiments=exp_list,
                               past_experiments=past_experiments, upload=upload)

    @app.route('/experiments/run', methods=['POST'])
    def run_experiments():
        upload = get_latest_upload()
        if not upload:
            return jsonify({"error": "No data uploaded"}), 400

        df = posts_to_df(upload['id'])
        profile = build_profile(df)

        data = request.get_json()
        experiment_names = data.get('experiments', [])
        custom_prompt = data.get('custom_prompt', '')

        results = []

        for name in experiment_names:
            result = run_experiment(name, profile)
            if result['status'] == 'success':
                save_experiment(upload['id'], result['name'], result['description'],
                                result.get('data') or result.get('raw', ''),
                                result['time_seconds'])
            results.append(result)

        if custom_prompt:
            result = run_custom_experiment(custom_prompt, profile)
            if result['status'] == 'success':
                save_experiment(upload['id'], 'custom', custom_prompt,
                                result.get('data') or result.get('raw', ''),
                                result['time_seconds'])
            results.append(result)

        return jsonify({"results": results})

    # --- Suggestions ---
    @app.route('/suggestions')
    def suggestions_page():
        upload = get_latest_upload()
        suggestions = get_suggestions(upload['id']) if upload else []
        return render_template('suggestions.html', suggestions=suggestions, upload=upload)

    @app.route('/suggestions/generate', methods=['POST'])
    def generate_suggestions_route():
        upload = get_latest_upload()
        if not upload:
            return jsonify({"error": "No data uploaded"}), 400

        df = posts_to_df(upload['id'])
        profile = build_profile(df)
        result = generate_suggestions(profile)

        if result['status'] == 'success' and result['suggestions']:
            save_suggestions(upload['id'], result['suggestions'])

        return jsonify(result)

    @app.route('/suggestions/<int:sid>/used', methods=['POST'])
    def mark_used(sid):
        mark_suggestion_used(sid)
        return jsonify({"status": "ok"})

    return app
