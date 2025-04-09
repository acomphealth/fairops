from pathlib import Path
import os
from dotenv import load_dotenv


def get_env_path(create_if_not_exist=False):
    home_path = Path.home()

    env_paths = {
        "cwd": ".env",
        "home_config": os.path.join(home_path, ".config", "fairops", ".env")
    }

    selected_env = None
    for key, env_path in env_paths.items():
        if os.path.exists(env_path):
            selected_env = env_path
            break

    if selected_env is None and create_if_not_exist:
        selected_env = env_paths["home_config"]
        os.makedirs(os.path.dirname(selected_env))

    return selected_env


def load_fairops_env():
    env_path = get_env_path()
    if env_path is not None:
        load_dotenv(env_path, override=True)
