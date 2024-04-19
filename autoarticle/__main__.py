import click
from core.create import create
from core.generate import generate

# from core.info import info
from core.upload import upload
from db.manage import create_db
from db.models import db_obj


@click.group()
def cli():
    pass


cli.add_command(create)
cli.add_command(generate)
cli.add_command(upload)
# cli.add_command(info)


if __name__ == "__main__":
    create_db(db_obj)
    cli()
