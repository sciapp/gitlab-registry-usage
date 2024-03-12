#!/usr/bin/env python3

from gitlab_registry_usage import GitLabRegistry
import json
import os
import sys
from urllib.parse import urlparse

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

gitlab_base_url = c['gitlab_base_url']
registry_base_url = c['registry_base_url']
username = c['username']
access_token = c['access_token']

def getRegistry(cache_file, config):
    if os.path.exists(cache_file):
        print("loading cache: {}".format(cache_file))
        with open(cache_file) as f:
            data = json.load(f)
    else:
        gitlab_registry = GitLabRegistry(
            gitlab_base_url, registry_base_url, username, access_token
        )
        data = {}
        data['registry'] = urlparse(config['registry_base_url']).netloc
        data['gitlab_base_url'] = config['gitlab_base_url']
        data['registry_base_url'] = config['registry_base_url']
        data['repository_tags'] = gitlab_registry.repository_tags
        data['repository_sizes'] = gitlab_registry.repository_sizes
        data['repository_disk_sizes'] = gitlab_registry.repository_disk_sizes
        data['tag_sizes'] = gitlab_registry.tag_sizes
        data['tag_disk_sizes'] = gitlab_registry.tag_disk_sizes
        data['total_size'] = gitlab_registry.total_size
        data['total_disk_size'] = gitlab_registry.total_disk_size

        with open(cache_file, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '))
    return data

gitlab_registry = getRegistry(cache_file='{hostname}.json'.format(hostname=urlparse(c['registry_base_url']).netloc), config=c)

for repository in gitlab_registry['repository_tags'].keys():
    repository_tags = gitlab_registry['repository_tags'][repository]
    repository_size = gitlab_registry['repository_sizes'][repository]
    repository_disk_size = gitlab_registry['repository_disk_sizes'][repository]
    tag_sizes = gitlab_registry['tag_sizes'][repository]
    tag_disk_sizes = gitlab_registry['tag_disk_sizes'][repository]
    if (
        repository_tags is not None and repository_size is not None
        and repository_disk_size is not None and tag_sizes is not None
        and tag_disk_sizes is not None
    ):
        print(
            '{}: repository size: {}, repository disk size: {}'.format(
                repository, repository_size, repository_disk_size
            )
        )
        for tag in repository_tags:
            print(
                '{}: tag size: {}, tag disk size: {}'.format(
                    tag, tag_sizes[tag], tag_disk_sizes[tag]
                )
            )
    else:
        print('{}: no further information available'.format(repository))
    print()
print(
    ('total size: {}, total disk size: {}').format(
        gitlab_registry['total_size'], gitlab_registry['total_disk_size']
    )
)
