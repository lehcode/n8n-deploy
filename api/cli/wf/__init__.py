#!/usr/bin/env python3
"""
Workflow management commands for n8n-deploy CLI.

Provides a consistent 'wf' command group for all workflow operations including:
- Basic operations: add, list, delete, search, stats
- Server operations: pull, push, server
- Metadata operations: link
"""

import click

from ..app import CustomGroup, handle_verbose_flag


@click.group(cls=CustomGroup)
@click.option(
    "-v",
    "--verbose",
    count=True,
    expose_value=False,
    is_eager=True,
    callback=handle_verbose_flag,
    help="Verbosity level (-v, -vv)",
)
def wf() -> None:
    """🔄 Workflow management commands"""
    pass


# Import and register commands
from .add import add
from .delete import delete
from .link import link
from .list_cmd import list_cmd, list_server
from .pull import pull
from .push import push
from .search import search
from .stats import stats

wf.add_command(add)
wf.add_command(list_cmd, name="list")
wf.add_command(delete)
wf.add_command(search)
wf.add_command(stats)
wf.add_command(pull)
wf.add_command(push)
wf.add_command(list_server, name="server")
wf.add_command(link)

__all__ = ["wf"]
