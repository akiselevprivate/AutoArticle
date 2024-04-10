import click
from core.create import create
from core.info import info
from core.upload import upload
from db.manage import create_db
from db.models import db_obj

# import asyncio
# import signal


# # Signal handler function
# def signal_handler(signum, frame):
#     print("Received Ctrl+C. Cancelling tasks...")
#     for task in asyncio.all_tasks():
#         task.cancel()


# # Set up the signal handler for Ctrl+C (SIGINT)
# signal.signal(signal.SIGINT, signal_handler)


@click.group()
def cli():
    pass


cli.add_command(create)
cli.add_command(upload)
cli.add_command(info)


if __name__ == "__main__":
    create_db(db_obj)
    cli()
