from app.app import create_app


# Gunicorn entry point - used in production and referenced in the`Dockerfile`
def app():
    return create_app()


# Flask entry point - used for local development
def run_app():
    app = create_app()
    app.run(port=4567)
    return app


if __name__ == "__main__":
    run_app()
