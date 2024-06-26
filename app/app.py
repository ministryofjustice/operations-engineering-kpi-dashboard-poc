import logging

from dash import Dash, dcc, html
from flask import Flask

from app.config.app_config import app_config
from app.config.logging_config import configure_logging
from app.config.routes_config import configure_routes
from app.services.database_service import DatabaseService
from app.services.figure_service import FigureService

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging(app_config.logging_level)

    logger.info("Starting app...")

    server = Flask(__name__)

    server.database_service = DatabaseService()
    server.figure_service = FigureService(server.database_service)

    configure_routes(server)

    logger.info("Populating stub data...")
    server.database_service.create_indicators_table()
    server.database_service.clean_stubbed_indicators_table()
    server.database_service.add_stubbed_indicators()

    app = Dash(__name__, server=server, url_base_pathname="/dashboard/")
    app.title = "⚙️ OE - KPI Dashboard"
    app.layout = create_dashboard(server.figure_service)

    logger.info("Running app...")

    return app.server


def create_dashboard(figure_service: FigureService):
    def dashboard():
        return html.Div(
            children=[
                html.H1("🤩 Live Data 🤩"),
                dcc.Graph(
                    figure=figure_service.get_number_of_repositories_with_standards_label_dashboard(),
                    style={"width": "100%", "height": "500px", "display": "inline-block"},
                ),
                html.H1("🙈 Stub Data 🙈"),
                dcc.Graph(
                    figure=figure_service.get_stubbed_number_of_repositories_with_standards_label_dashboard(),
                    style={"width": "33%", "height": "500px", "display": "inline-block"},
                ),
                dcc.Graph(
                    figure=figure_service.get_stubbed_number_of_repositories_archived_by_automation(),
                    style={"width": "33%", "height": "500px", "display": "inline-block"},
                ),
                dcc.Graph(
                    figure=figure_service.get_stubbed_sentry_transactions_used(),
                    style={"width": "33%", "height": "500px", "display": "inline-block"},
                ),
                dcc.Graph(
                    figure=figure_service.get_support_stats(),
                    style={"width": "100%", "height": "500px", "display": "inline-block"},
                ),
                dcc.Graph(
                    figure=figure_service.get_github_actions_quota_usage(),
                    style={"width": "100%", "height": "500px", "display": "inline-block"},
                ),
            ],
            style={"padding": "0px", "margin": "0px", "background-color": "black"},
        )

    return dashboard
