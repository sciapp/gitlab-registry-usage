#!/usr/bin/env python3

import yaml
import json
import os
import sys
import binascii
from gitlab_registry_usage.cli import human_size
from urllib.parse import urlparse

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def parse_config(filename):
    """Parse configuration file.

    Args:
      filename: Path to the configuration file to parse.
    Returns:
      Dictionary of values defined in the file.
    """
    with open(filename) as f:
        data = f.read()
        compiled = compile(data, filename, "exec")
        result = { 'main': sys.modules[__name__] }
        eval(compiled, result)
        return result

c = parse_config(sys.argv[1])

registry_base_url = c['registry_base_url']

def getRegistry(cache_file):
    with open(cache_file) as f:
        data = json.load(f)
    return data

gitlab_registry = getRegistry(cache_file='{hostname}.json'.format(hostname=urlparse(c['registry_base_url']).netloc))

def format_printable(gitlab_registry):
    for repository, tags in gitlab_registry['repository_tags'].items():
        if tags is None:
            continue
        disk_size = human_size(gitlab_registry['repository_disk_sizes'][repository])
        repo_size = human_size(gitlab_registry['repository_sizes'][repository])
        print("\n# {repository} {repo_size} {disk_size}".format(repository=repository, repo_size=repo_size, disk_size=disk_size))
        for tag in tags:
            disk_size = human_size(gitlab_registry['tag_disk_sizes'][repository][tag])
            repo_size = human_size(gitlab_registry['tag_sizes'][repository][tag])
            print("  {repository}/{tag} {repo_size} {disk_size}".format(repository=repository, tag=tag, repo_size=repo_size, disk_size=disk_size))

    print("\n# total: {size}".format(size=human_size(gitlab_registry['total_size'])))

def is_hex(string):
    try:
        res = binascii.unhexlify(string)
    except binascii.Error:
        return False
    return True

def format_lstags(gitlab_registry):
    repos = []
    registry = gitlab_registry['registry']

    for repository, tags in gitlab_registry['repository_tags'].items():
        if tags is None:
            continue
        if repository.endswith('/builds') or repository.endswith('/build') or repository.endswith('/test') or repository.endswith('/dev'):
            print("# Skipped image: {image}".format(image=repository))
            continue
        for tag in tags:
            image = '{registry}/{repo}={tag}'.format(registry=registry, repo=repository, tag=tag)
            if len(tag) == 40 and is_hex(tag):
                print("# Skipped tag: {repo}:{tag}".format(repo=repository, tag=tag))
                continue
            repos.append(image)

    data = {}
    data['lstags'] = {}
    data['lstags']['repositories'] = repos

    return yaml.dump(data, Dumper=Dumper,  default_flow_style=False)

print(format_lstags(gitlab_registry))
#format_printable(gitlab_registry)
