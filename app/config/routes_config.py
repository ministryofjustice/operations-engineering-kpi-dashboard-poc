from flask import Flask

from app.routes.api_route import api_route
from app.routes.index_route import index_route


def configure_routes(app: Flask) -> None:
    app.register_blueprint(api_route, url_prefix="/api")
    app.register_blueprint(index_route, url_prefix="/")
