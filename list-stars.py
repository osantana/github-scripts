#!/usr/bin/env python3
import csv
import sys
import time
from datetime import datetime

import click
from github3 import login
from github3.users import User
from prettyconf import config
from tqdm import tqdm


RATE_LIMIT_RESET_THRESHOLD = 10
USER_FIELDS = (
    'name',
    'email',
    'location',
    'company',
    'hireable',
    'url',
)


def wait_until(reset_timestamp):
    current_timestamp = datetime.utcnow()
    wait_time = reset_timestamp - current_timestamp

    wait_seconds = int(round(wait_time.total_seconds()))
    for _ in tqdm(range(wait_seconds), desc=f"Waiting for rate limit reset", unit="s", file=sys.stderr):
        time.sleep(1)


@click.command()
@click.argument('repository')
@click.option('-O', '--output', type=click.File('w', encoding='utf-8'), default=sys.stdout)
def main(repository, output):
    """Export list of Stars of REPOSITORY (eg. `account/repo')"""
    try:
        account, repo_name = repository.split('/')
    except TypeError:
        click.echo(f'Invalid repository name: {repository}')
        return 1

    token = config("GITHUB_TOKEN")
    github = login(token=token)

    repo = github.repository(account, repo_name)

    writer = csv.DictWriter(output, fieldnames=USER_FIELDS)
    writer.writeheader()

    for stargazer in repo.stargazers():
        user: User = github.user(stargazer.login)
        rate_limit = user.ratelimit_remaining
        if rate_limit < RATE_LIMIT_RESET_THRESHOLD:
            reset_timestamp = datetime.utcfromtimestamp(github.rate_limit()['resources']['core']['reset'])
            wait_until(reset_timestamp)
        writer.writerow({
            'name': (user.name or '').strip(),
            'email': (user.email or '').strip(),
            'location': (user.location or '').strip(),
            'company': (user.company or '').strip(),
            'hireable': user.hireable and '1' or '0',
            'url': (user.html_url or '').strip(),
        })


if __name__ == '__main__':
    sys.exit(int(main() or 0))
