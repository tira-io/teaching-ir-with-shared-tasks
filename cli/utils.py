"""
Generic helpers shared across the CLI modules.
"""

from slugify import slugify


def group_user_name(project_prefix: str, group: str) -> str:
    group = slugify(group)
    return f"{project_prefix}-{group}"
