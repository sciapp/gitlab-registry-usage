# GitLab-Registry-Usage

## Introduction

*GitLab-Registry-Usage* is a package for querying the sizes of Docker images stored in a GitLab registry. The package
has been created because it is not possible to monitor sizes of GitLab registry images with GitLab web monitoring tools
(GitLab version <= 10.5.4).

## Installation

The latest version is available from PyPI:

```bash
pip install gitlab-registry-usage
```

## Usage

### Command Line Interface

After installing with `pip`, a `gitlab-registry-usage` command is available:

```bash
$ gitlab-registry-usage --help
usage: gitlab-registry-usage [-h] [-g GITLAB_SERVER] [-r REGISTRY_SERVER]
                             [-s {name,size,disksize}] [-c CREDENTIALS_FILE]
                             [-u USERNAME] [-V]

gitlab-registry-usage is a utility for querying the memory usage of images in a GitLab registry.

optional arguments:
  -h, --help            show this help message and exit
  -g GITLAB_SERVER, --gitlab-server GITLAB_SERVER
                        GitLab server hostname (for example `mygitlab.com`)
  -r REGISTRY_SERVER, --registry-server REGISTRY_SERVER
                        GitLab registry server hostname (for example
                        `registry.mygitlab.com`)
  -s {name,size,disksize}, --sort {name,size,disksize}
                        sorting order (default: name)
  -c CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                        path to a file containing username and password/access
                        token (on two separate lines)
  -u USERNAME, --user USERNAME
                        user account for querying the GitLab API (default:
                        root)
  -V, --version         print the version number and exit
```

You should specify a GitLab server hostname (`-g`), a GitLab registry server hostname (`-r`) and either a credentials
file (`-c`) or username (`-u`) and password (read from stdin).

### API

The module offers a high level `GitLabRegistry` class to query the image catalog and image sizes. This example prints
all images, tags and their sizes:

```python
from gitlab_registry_usage.registry import GitLabRegistry

# TODO: set these values!
gitlab_base_url = ''
registry_base_url = ''
username = 'root'
access_token = '0000000000'

gitlab_registry = GitLabRegistry(
    gitlab_base_url, registry_base_url, username, access_token
)
for image in gitlab_registry.image_tags.keys():
    image_tags = gitlab_registry.image_tags[image]
    image_size = gitlab_registry.image_sizes[image]
    image_disk_size = gitlab_registry.image_disk_sizes[image]
    tag_sizes = gitlab_registry.tag_sizes[image]
    tag_disk_sizes = gitlab_registry.tag_disk_sizes[image]
    if (
        image_tags is not None and image_size is not None
        and image_disk_size is not None and tag_sizes is not None
        and tag_disk_sizes is not None
    ):
        print(
            '{}: image size: {}, image disk size: {}'.format(
                image, image_size, image_disk_size
            )
        )
        for tag in image_tags:
            print(
                '{}: tag size: {}, tag disk size: {}'.format(
                    tag, tag_sizes[tag], tag_disk_sizes[tag]
                )
            )
    else:
        print('{}: no further information available'.format(image))
    print()
print(
    ('total size: {}, total disk size: {}').format(
        gitlab_registry.total_size, gitlab_registry.total_disk_size
    )
)
```
