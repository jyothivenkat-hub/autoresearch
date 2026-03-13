"""Start the Twitter Optimizer web app."""

from webapp.app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n  Twitter Optimizer running at: http://localhost:5001\n")
    app.run(debug=True, port=5001)
