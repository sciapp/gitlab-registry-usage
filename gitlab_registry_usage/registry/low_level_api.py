import json
import requests
from typing import List, Optional


class AuthTokenError(Exception):
    pass


class CatalogReadError(Exception):
    pass


class TagsReadError(Exception):
    pass


class LayersReadError(Exception):
    pass


class LayerSizeReadError(Exception):
    pass


class ImageDeleteError(Exception):
    pass


def _auth_token(auth_url: str, username: str, password: str) -> Optional[str]:
    response = requests.get(auth_url, auth=(username, password))
    if response.status_code != 200:
        return None
    try:
        json_response = response.json()
    except json.decoder.JSONDecodeError:
        return None
    if 'token' not in json_response:
        return None
    return str(json_response['token'])


def get_catalog_auth_token(gitlab_url: str, username: str, password: str) -> str:
    catalog_auth_url = '{base}jwt/auth?client_id=docker&service=container_registry&scope=registry:catalog:*'.format(
        base=gitlab_url
    )
    auth_token = _auth_token(catalog_auth_url, username, password)
    if auth_token is None:
        raise AuthTokenError
    return auth_token


def get_repository_auth_token(gitlab_url: str, username: str, password: str, repository: str) -> str:
    repo_auth_url = '{base}jwt/auth?client_id=docker&service=container_registry&scope=repository:{repository}:*'.format(
        base=gitlab_url, repository=repository
    )
    auth_token = _auth_token(repo_auth_url, username, password)
    if auth_token is None:
        raise AuthTokenError
    return auth_token


def get_registry_catalog(registry_url: str, auth_token: str) -> List[str]:
    catalog_url = '{base}v2/_catalog'.format(base=registry_url)
    response = requests.get(catalog_url, headers={'Authorization': 'Bearer ' + auth_token})
    if response.status_code != 200:
        raise CatalogReadError
    try:
        json_response = response.json()
    except json.decoder.JSONDecodeError:
        raise CatalogReadError
    if 'repositories' not in json_response:
        raise CatalogReadError
    if json_response['repositories'] is None:
        return []
    return [str(repository) for repository in response.json()['repositories']]


def get_repository_tags(registry_url: str, auth_token: str, repository: str) -> List[str]:
    repo_tags_url = '{base}v2/{repository}/tags/list'.format(base=registry_url, repository=repository)
    response = requests.get(repo_tags_url, headers={'Authorization': 'Bearer ' + auth_token})
    if response.status_code != 200:
        raise TagsReadError
    try:
        json_response = response.json()
    except json.decoder.JSONDecodeError:
        raise TagsReadError
    if 'tags' not in json_response:
        raise TagsReadError
    if json_response['tags'] is None:
        return []
    return [str(tag) for tag in response.json()['tags']]


def get_tag_layers(registry_url: str, auth_token: str, repository: str, tag: str) -> List[str]:
    tag_layers_url = '{base}v2/{repository}/manifests/{tag}'.format(base=registry_url, repository=repository, tag=tag)
    response = requests.get(tag_layers_url, headers={'Authorization': 'Bearer ' + auth_token})
    if response.status_code != 200:
        raise LayersReadError
    try:
        json_response = response.json()
    except json.decoder.JSONDecodeError:
        raise LayersReadError
    if 'fsLayers' not in json_response:
        raise LayersReadError
    fs_layers = []  # type: List[str]
    if json_response['fsLayers'] is None:
        return fs_layers
    for layer in json_response['fsLayers']:
        if 'blobSum' not in layer:
            raise LayersReadError
        fs_layers.append(str(layer['blobSum']))
    return fs_layers


def get_layer_size(registry_url: str, auth_token: str, repository: str, layer: str) -> int:
    blob_url = '{base}v2/{repository}/blobs/{layer}'.format(base=registry_url, repository=repository, layer=layer)
    response = requests.head(blob_url, headers={'Authorization': 'Bearer ' + auth_token})

    # Handle redirect (S3 Backend for example)
    if response.status_code == 307:
        if 'Location' not in response.headers:
            raise LayerSizeReadError
        response = requests.head(response.headers['Location'])

    if response.status_code != 200:
        raise LayerSizeReadError
    response_header = response.headers
    if 'Content-Length' not in response_header:
        raise LayerSizeReadError
    try:
        content_length = int(response_header['Content-Length'])
    except ValueError:
        raise LayerSizeReadError
    return content_length


def delete_image(registry_url: str, auth_token: str, repository: str, image_hash: str) -> None:
    image_url = '{base}v2/{repository}/manifests/{image_hash}'.format(
        base=registry_url, repository=repository, image_hash=image_hash
    )
    response = requests.delete(image_url, headers={'Authorization': 'Bearer ' + auth_token})
    if response.status_code != 202:
        raise ImageDeleteError
