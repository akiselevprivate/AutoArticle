import click
from core.create import create
from core.upload import upload


@click.group()
def cli():
    pass


cli.add_command(create)
cli.add_command(upload)


if __name__ == "__main__":
    cli()
