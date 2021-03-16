#!/usr/bin/env python3

import argparse
import getpass
import logging
import math
import os
import re
import subprocess
import sys
from typing import cast, Any, Callable
from yacl import setup_colored_stderr_logging
from .registry import GitLabRegistry, AuthTokenError
from ._version import __version__, __version_info__  # noqa: F401 # pylint: disable=unused-import

__author__ = "Ingo Meyer"
__email__ = "i.meyer@fz-juelich.de"
__copyright__ = "Copyright © 2018 Forschungszentrum Jülich GmbH. All rights reserved."
__license__ = "MIT"

DEFAULT_ORDER = "name"
DEFAULT_USER = "root"


logger = logging.getLogger(__name__)


class MissingServerNameError(Exception):
    pass


class InvalidServerNameError(Exception):
    pass


class CredentialsReadError(Exception):
    pass


def has_terminal_color() -> bool:
    try:
        return os.isatty(sys.stderr.fileno()) and int(subprocess.check_output(["tput", "colors"])) >= 8
    except subprocess.CalledProcessError:
        return False


class TerminalColorCodes:
    if has_terminal_color():
        RED = "\033[31;1m"
        GREEN = "\033[32;1m"
        YELLOW = "\033[33;1m"
        BLUE = "\033[34;1m"
        PURPLE = "\033[35;1m"
        CYAN = "\033[36;1m"
        GRAY = "\033[36;1m"
        RESET = "\033[0m"
    else:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        PURPLE = ""
        CYAN = ""
        GRAY = ""
        RESET = ""


class AttributeDict(dict):
    def __getattr__(self, attr: str) -> Any:
        return self[attr]

    def __setattr__(self, attr: str, value: Any) -> None:
        self[attr] = value


def human_size(size: int) -> str:
    suffixes = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    order = int(math.log2(size) / 10) if size else 0
    return "{:.4g} {}".format(size / (1 << (order * 10)), suffixes[order])


def get_argumentparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
%(prog)s is a utility for querying the memory usage of repositories in a GitLab registry.
""",
    )
    parser.add_argument(
        "-g",
        "--gitlab-server",
        action="store",
        dest="gitlab_server",
        help="GitLab server hostname (for example `mygitlab.com`)",
    )
    parser.add_argument(
        "-r",
        "--registry-server",
        action="store",
        dest="registry_server",
        help="GitLab registry server hostname (for example `registry.mygitlab.com`)",
    )
    parser.add_argument(
        "-s",
        "--sort",
        action="store",
        dest="sorting_order",
        choices=("name", "size", "disksize"),
        default=DEFAULT_ORDER,
        help="sorting order (default: %(default)s)",
    )
    parser.add_argument(
        "-c",
        "--credentials-file",
        action="store",
        dest="credentials_file",
        type=cast(Callable[[str], str], os.path.abspath),
        help="path to a file containing username and password/access token (on two separate lines)",
    )
    parser.add_argument(
        "-u",
        "--user",
        action="store",
        dest="username",
        default=DEFAULT_USER,
        help="user account for querying the GitLab API (default: %(default)s)",
    )
    parser.add_argument(
        "-V", "--version", action="store_true", dest="print_version", help="print the version number and exit"
    )
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v", "--verbose", action="store_true", dest="verbose", help="be verbose",
    )
    verbosity_group.add_argument(
        "--debug", action="store_true", dest="debug", help="print debug messages",
    )
    return parser


def parse_arguments() -> AttributeDict:
    parser = get_argumentparser()
    args = AttributeDict({key: value for key, value in vars(parser.parse_args()).items()})
    if not args.print_version and (args.gitlab_server is None or args.registry_server is None):
        if args.gitlab_server is None and args.registry_server is None:
            raise MissingServerNameError("Neither a GitLab server nor a registry server is given.")
        elif args.gitlab_server is None:
            raise MissingServerNameError("No GitLab server is given.")
        else:
            raise MissingServerNameError("No registry server is given.")
    if not args.print_version:
        for server in ("gitlab_server", "registry_server"):
            match_obj = re.match(r"(?:https?//)?(.+)/?", args[server])
            if match_obj:
                args[server] = match_obj.group(1)
            else:
                raise InvalidServerNameError("{} is not a valid server name.".format(server))
        if args.credentials_file is not None:
            try:
                with open(args.credentials_file, "r") as f:
                    for key in ("username", "password"):
                        args[key] = f.readline().strip()
            except IOError:
                raise CredentialsReadError("Could not read credentials file {}.".format(args.credentials_file))
        elif args.username is not None:
            args["password"] = getpass.getpass()
        else:
            raise CredentialsReadError("Could not get credentials for the GitLab web api.")

    return args


def query_gitlab_registry(
    gitlab_server: str, registry_server: str, username: str, password: str, sorting_order: str
) -> None:
    gitlab_base_url = "https://{}/".format(gitlab_server)
    registry_base_url = "https://{}/".format(registry_server)
    gitlab_registry = GitLabRegistry(gitlab_base_url, registry_base_url, username, password)
    label_column_width = max(
        [len(repository) for repository in gitlab_registry.registry_catalog]
        + [len(tag) - 4 for tags in gitlab_registry.repository_tags for tag in tags]
    )

    if sorting_order == "size":

        def repository_sort_key_func(repository: str) -> Any:
            repository_size = gitlab_registry.repository_sizes[repository]
            return repository_size if repository_size is not None else -1

        def tag_sort_key_func_for_repository(repository: str) -> Callable[[str], Any]:
            tag_sizes = gitlab_registry.tag_sizes[repository]

            def tag_sort_key_func(tag: str) -> Any:
                return tag_sizes[tag] if tag_sizes is not None else -1

            return tag_sort_key_func

    elif sorting_order == "disksize":

        def repository_sort_key_func(repository: str) -> Any:
            repository_disk_size = gitlab_registry.repository_disk_sizes[repository]
            return repository_disk_size if repository_disk_size is not None else -1

        def tag_sort_key_func_for_repository(repository: str) -> Callable[[str], Any]:
            tag_disk_sizes = gitlab_registry.tag_disk_sizes[repository]

            def tag_sort_key_func(tag: str) -> Any:
                return tag_disk_sizes[tag] if tag_disk_sizes is not None else -1

            return tag_sort_key_func

    else:

        def repository_sort_key_func(repository: str) -> Any:
            return repository

        def tag_sort_key_func_for_repository(repository: str) -> Callable[[str], Any]:  # pylint:disable=unused-argument
            def tag_sort_key_func(tag: str) -> Any:
                return tag

            return tag_sort_key_func

    sorted_repositories = sorted(gitlab_registry.repository_tags.keys(), key=repository_sort_key_func)
    for repository in sorted_repositories:
        repository_tags = gitlab_registry.repository_tags[repository]
        repository_size = gitlab_registry.repository_sizes[repository]
        repository_disk_size = gitlab_registry.repository_disk_sizes[repository]
        tag_sizes = gitlab_registry.tag_sizes[repository]
        tag_disk_sizes = gitlab_registry.tag_disk_sizes[repository]
        if (
            repository_tags is not None
            and repository_size is not None
            and repository_disk_size is not None
            and tag_sizes is not None
            and tag_disk_sizes is not None
        ):
            print(
                (
                    "{}{:>"
                    + str(label_column_width)
                    + "}{}:     repository size: {}{:>9}{}, repository disk size: {}{:>9}{}"
                ).format(
                    TerminalColorCodes.CYAN,
                    repository,
                    TerminalColorCodes.RESET,
                    TerminalColorCodes.YELLOW,
                    human_size(repository_size),
                    TerminalColorCodes.RESET,
                    TerminalColorCodes.YELLOW,
                    human_size(repository_disk_size),
                    TerminalColorCodes.RESET,
                )
            )
            sorted_tags = sorted(repository_tags, key=tag_sort_key_func_for_repository(repository))
            for tag in sorted_tags:
                print(
                    (
                        "{}{:>" + str(label_column_width + 4) + "}{}:   tag size: {}{:>9}{},   tag disk size: {}{:>9}{}"
                    ).format(
                        TerminalColorCodes.BLUE,
                        tag,
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.GREEN,
                        human_size(tag_sizes[tag]),
                        TerminalColorCodes.RESET,
                        TerminalColorCodes.GREEN,
                        human_size(tag_disk_sizes[tag]),
                        TerminalColorCodes.RESET,
                    )
                )
        else:
            print(
                ("{}{:>" + str(label_column_width) + "}{}:     no further information available").format(
                    TerminalColorCodes.CYAN, repository, TerminalColorCodes.RESET
                )
            )
        print()
    print(
        ("{:" + str(label_column_width + 6) + "}total size: {}{:>9}{}, total disk size: {}{:>9}{}").format(
            "",
            TerminalColorCodes.RED,
            human_size(gitlab_registry.total_size),
            TerminalColorCodes.RESET,
            TerminalColorCodes.RED,
            human_size(gitlab_registry.total_disk_size),
            TerminalColorCodes.RESET,
        )
    )


def setup_stderr_logging(args: AttributeDict) -> None:
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    setup_colored_stderr_logging(format_string="[%(levelname)s] %(message)s")


def main() -> None:
    args = parse_arguments()
    if args.print_version:
        print("{}, version {}".format(os.path.basename(sys.argv[0]), __version__))
        sys.exit(0)
    setup_stderr_logging(args)
    try:
        query_gitlab_registry(
            args.gitlab_server, args.registry_server, args.username, args.password, args.sorting_order
        )
    except AuthTokenError:
        print(
            "{}Failed{} to get an auth token. Is the username/password correct?".format(
                TerminalColorCodes.RED, TerminalColorCodes.RESET
            ),
            file=sys.stderr,
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
