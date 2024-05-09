import logging

from dash import Dash, dcc, html
from flask import Flask

from app.config.app_config import app_config
from app.config.logging_config import configure_logging
from app.services.dashboard_service import FigureService
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging(app_config.logging_level)

    logger.info("Starting app...")

    server = Flask(__name__)

    database_service = DatabaseService()
    figure_service = FigureService(database_service)

    logger.info("Populating stub data...")
    database_service.create_indicators_table()
    database_service.clean_indicators_table()
    database_service.add_data()

    app = Dash(__name__, server=server)

    app.layout = html.Div(
        children=[
            dcc.Graph(
                figure=figure_service.get_number_of_repositories_with_standards_label_dashboard(),
                style={"width": "33%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=figure_service.get_number_of_repositories_archived_by_automation(),
                style={"width": "33%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=figure_service.get_sentry_transactions_used(),
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

    logger.info("Running app...")

    return app.server
