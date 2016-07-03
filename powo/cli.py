# -*- coding: utf-8 -*-

import click

from .ansible import run


@click.command()
def main(args=None):
    """Console script for powo"""
    run()


if __name__ == "__main__":
    main()
