import datetime
import logging
from typing import Any

import pandas as pd
import plotly.express as px
import psycopg2
from dash import Dash, dcc, html
from flask import Flask

from app.config.app_config import app_config
from app.config.logging_config import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging(app_config.logging_level)

    logger.info("Starting app...")

    logger.info("Populating stub data...")
    create_indicators_table()
    clean_indicators_table()
    add_data()

    logger.info("Retrieving stub data...")
    sentry_transaction_quota_consumed = pd.DataFrame(get_indicator("SENTRY_DAILY_TRANSACTION_USAGE"), columns=["timestamp", "count"]).sort_values(
        by="timestamp", ascending=True
    )
    number_of_repositories_archived_by_automation = pd.DataFrame(
        get_indicator("REPOSITORIES_ARCHIVED_BY_AUTOMATION"), columns=["timestamp", "count"]
    ).sort_values(by="timestamp", ascending=True)
    number_of_repos_with_standards_label_df = pd.DataFrame(get_indicator("REPOSITORIES_WITH_STANDARDS_LABEL"), columns=["timestamp", "count"]).sort_values(
        by="timestamp", ascending=True
    )
    support_stats_csv = pd.read_csv("data/support-stats.csv")
    logging.info(support_stats_csv)
    support_stats_csv_pivoted = pd.melt(
        support_stats_csv,
        value_vars=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        id_vars=["Request Type", "Total"],
        value_name="Count",
        var_name="Month",
        ignore_index=True,
    )
    logging.info(support_stats_csv_pivoted)
    github_usage_csv = pd.read_csv("data/github_actions_private_and_internal.csv").sort_values(by="Date", ascending=True)
    logging.info(github_usage_csv)
    github_actions = github_usage_csv[github_usage_csv["Product"] == "Actions"]
    logging.info(github_actions)
    github_actions_summed = github_actions.groupby(by="Date", as_index=False).agg("sum")
    github_actions_summed["Date"] = pd.to_datetime(github_actions_summed["Date"])
    logging.info(github_actions_summed)

    logger.info("Creating app...")
    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            dcc.Graph(
                figure=px.line(
                    number_of_repos_with_standards_label_df,
                    x="timestamp",
                    y="count",
                    title="🏷️ Number of Repositories With Standards Label",
                    markers=True,
                    template="plotly_dark",
                ).add_hline(y=0),
                style={"width": "33%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=px.line(
                    number_of_repositories_archived_by_automation,
                    x="timestamp",
                    y="count",
                    title="👴 Number of Repositories Archived By Automation",
                    markers=True,
                    template="plotly_dark",
                ).add_hline(y=0),
                style={"width": "33%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=px.line(
                    sentry_transaction_quota_consumed,
                    x="timestamp",
                    y="count",
                    title="👀 Sentry Transactions Used",
                    markers=True,
                    template="plotly_dark",
                )
                .add_hline(y=967741, annotation_text="Max Daily Usage")
                .add_hrect(y0=(967741 * 0.8), y1=967741, line_width=0, fillcolor="red", opacity=0.2, annotation_text="Alert Threshold"),
                style={"width": "33%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=px.line(
                    support_stats_csv_pivoted,
                    x="Month",
                    y="Count",
                    color="Request Type",
                    title="🏋️ Support Stats",
                    markers=True,
                    template="plotly_dark",
                ),
                style={"width": "100%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=px.line(
                    github_actions_summed,
                    x="Date",
                    y="Quantity",
                    title="💥 GitHub Quota Usage",
                    markers=True,
                    template="plotly_dark",
                    hover_data=["Price Per Unit ($)"],
                )
                .add_hline(y=github_actions_summed["Quantity"].mean(), line_dash="dash", annotation_text="Average Daily Usage")
                .add_hline(y=(40000 / 31), annotation_text="Max Daily Actions Usage Usage")
                .add_hrect(y0=((40000 / 31) * 0.8), y1=(40000 / 31), line_width=0, fillcolor="red", opacity=0.2, annotation_text="Actions Alert Threshold"),
                style={"width": "100%", "height": "500px", "display": "inline-block"},
            ),
            dcc.Graph(
                figure=px.scatter(
                    github_actions_summed,
                    x="Date",
                    y="Quantity",
                    title="💥 GitHub Quota Usage - 28 Day Rolling Average",
                    trendline="rolling",
                    trendline_options=dict(window=28),
                    template="plotly_dark",
                    hover_data=["Price Per Unit ($)"],
                )
                .add_hline(y=(40000 / 31), annotation_text="Max Daily Actions Usage Usage")
                .add_hrect(y0=((40000 / 31) * 0.8), y1=(40000 / 31), line_width=0, fillcolor="red", opacity=0.2, annotation_text="Actions Alert Threshold"),
                style={"width": "100%", "height": "500px", "display": "inline-block"},
            ),
        ],
        style={"padding": "0px", "margin": "0px", "background-color": "black"},
    )

    logger.info("Running app...")

    return app.server


def execute_query(sql: str, values: list[Any] = []):
    with psycopg2.connect(
        dbname=app_config.postgres.db,
        user=app_config.postgres.user,
        password=app_config.postgres.password,
        host=app_config.postgres.host,
        port=app_config.postgres.port,
    ) as conn:
        logging.info("Connected to the PostgreSQL server.")
        cur = conn.cursor()
        cur.execute(sql, values)
        data = None
        try:
            data = cur.fetchall()
        except Exception as e:
            logging.error(e)
        conn.commit()
        return data


def get_indicator(indicator: str) -> list[tuple[Any, Any]]:
    return execute_query(sql="SELECT timestamp, count FROM indicators WHERE indicator = %s;", values=[indicator])


def create_indicators_table() -> None:
    execute_query(
        sql="""
                CREATE TABLE IF NOT EXISTS indicators (
                    id SERIAL PRIMARY KEY,
                    indicator varchar,
                    timestamp timestamp,
                    count integer
                );
            """
    )


def clean_indicators_table() -> None:
    execute_query(sql="DELETE FROM indicators")


def add_data():
    for values in [
        # SENTRY_DAILY_TRANSACTION_USAGE
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 20), 771761),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 21), 796740),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 22), 437108),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 23), 421906),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 24), 853259),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 25), 779597),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 26), 1249612),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 27), 906111),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 28), 418087),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 29), 413430),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 30), 880825),
        ("SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 5, 1), 792862),
        # REPOSITORIES_WITH_STANDARDS_LABEL
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 20), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 21), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 22), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 23), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 24), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 25), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 26), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 27), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 28), 11),
        ("REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 29), 11),
        # REPOSITORIES_ARCHIVED_BY_AUTOMATION
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 20), 1),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 21), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 22), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 23), 4),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 24), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 25), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 26), 1),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 27), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 28), 0),
        ("REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 29), 0),
    ]:
        execute_query("INSERT INTO indicators (indicator,timestamp, count) VALUES (%s, %s, %s);", values=values)
