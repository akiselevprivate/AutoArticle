import click
from core.create import create


@click.group()
def cli():
    pass


cli.add_command(create)


if __name__ == "__main__":
    cli()
