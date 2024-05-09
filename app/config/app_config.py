import os
from types import SimpleNamespace


def __get_env_var(name: str) -> str | None:
    return os.getenv(name)


def __get_env_var_as_boolean(name: str) -> bool | None:
    value = __get_env_var(name)

    if value is None:
        return False

    if value.lower() == "true":
        return True

    return False


app_config = SimpleNamespace(
    logging_level=__get_env_var("LOGGING_LEVEL"),
    postgres=SimpleNamespace(
        user=__get_env_var("POSTGRES_USER"),
        password=__get_env_var("POSTGRES_PASSWORD"),
        db=__get_env_var("POSTGRES_DB"),
        host=__get_env_var("POSTGRES_HOST"),
        port=__get_env_var("POSTGRES_PORT"),
    ),
    api_key=__get_env_var("API_KEY"),
)
