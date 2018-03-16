from typing import cast, Dict, List, NamedTuple, Optional, Tuple  # noqa: F401  # pylint: disable=unused-import
from .low_level_api import (  # noqa: F401  # pylint: disable=unused-import
    get_catalog_auth_token, get_registry_catalog, get_repository_auth_token, get_image_tags, get_tag_layers,
    get_layer_size, AuthTokenError, CatalogReadError, TagsReadError
)


# pylint: disable=attribute-defined-outside-init
class GitLabRegistry:
    def __init__(self, gitlab_url: str, registry_url: str, admin_username: str, admin_auth_token: str) -> None:
        self._gitlab_url = gitlab_url
        self._registry_url = registry_url
        self._admin_username = admin_username
        self._admin_auth_token = admin_auth_token
        self.clear()

    def clear(self) -> None:
        self._registry_catalog = None  # type: Optional[List[str]]
        self._image_layers = None  # type: Optional[Dict[str, Optional[Dict[str, List[str]]]]]
        self._primary_image_layers = None  # type: Optional[Dict[str, Optional[Dict[str, List[str]]]]]
        self._layer_sizes = None  # type: Optional[Dict[str, int]]
        self._tag_sizes = None  # type: Optional[Dict[str, Optional[Dict[str, int]]]]
        self._tag_disk_sizes = None  # type: Optional[Dict[str, Optional[Dict[str, int]]]]
        self._image_sizes = None  # type: Optional[Dict[str, Optional[int]]]
        self._image_disk_sizes = None  # type: Optional[Dict[str, Optional[int]]]
        self._total_size = None  # type: Optional[int]
        self._total_disk_size = None  # type: Optional[int]

    def update(self) -> None:
        self.clear()
        self._image_layers, self._layer_sizes = self._get_image_layers_and_layer_sizes()

    def _get_image_layers_and_layer_sizes(self) -> Tuple[Dict[str, Optional[Dict[str, List[str]]]], Dict[str, int]]:
        image_layers = {}  # type: Dict[str, Optional[Dict[str, List[str]]]]
        layer_sizes = {}  # type: Dict[str, int]
        for image in self.registry_catalog:
            repository_auth_token = get_repository_auth_token(
                self._gitlab_url, self._admin_username, self._admin_auth_token, image
            )
            try:
                current_image_layers = {}  # type: Dict[str, List[str]]
                image_tags = get_image_tags(self._registry_url, repository_auth_token, image)
                for tag in image_tags:
                    tag_layers = get_tag_layers(self._registry_url, repository_auth_token, image, tag)
                    current_image_layers[tag] = tag_layers
                    for layer in tag_layers:
                        layer_size = get_layer_size(self._registry_url, repository_auth_token, image, layer)
                        layer_sizes[layer] = layer_size
                image_layers[image] = current_image_layers
            except TagsReadError:
                image_layers[image] = None
        return image_layers, layer_sizes

    def _get_primary_image_layers(self) -> Dict[str, Optional[Dict[str, List[str]]]]:
        ImageWithTag = NamedTuple('ImageWithTag', [('image', str), ('tag', str)])
        layer_to_origin = {}  # type: Dict[str, ImageWithTag]
        for layer in self.layer_sizes:
            for image, tag_layers in self.image_layers.items():
                if tag_layers is None:
                    continue
                for tag, layers in tag_layers.items():
                    if layer in layers:
                        if layer not in layer_to_origin:
                            layer_to_origin[layer] = ImageWithTag(image, tag)
                        else:
                            current_origin_tag_layers = self.image_layers[layer_to_origin[layer].image]
                            if current_origin_tag_layers is not None and len(layers) < len(
                                current_origin_tag_layers[layer_to_origin[layer].tag]
                            ):
                                layer_to_origin[layer] = ImageWithTag(image, tag)
        primary_image_layers = {
            image: {
                tag: [layer for layer in layers if layer_to_origin[layer] == ImageWithTag(image, tag)]
                for tag, layers in tag_layers.items()
            } if tag_layers is not None else None
            for image, tag_layers in self.image_layers.items()
        }  # type: Dict[str, Optional[Dict[str, List[str]]]]
        return primary_image_layers

    @property
    def gitlab_url(self) -> str:
        return self._gitlab_url

    @property
    def registry_url(self) -> str:
        return self._registry_url

    @property
    def admin_username(self) -> str:
        return self._admin_username

    @property
    def admin_auth_token(self) -> str:
        return self._admin_auth_token

    @property
    def registry_catalog(self) -> List[str]:
        if self._registry_catalog is not None:
            return self._registry_catalog
        catalog_auth_token = get_catalog_auth_token(self._gitlab_url, self._admin_username, self._admin_auth_token)
        self._registry_catalog = get_registry_catalog(self._registry_url, catalog_auth_token)
        return self._registry_catalog

    @property
    def image_tags(self) -> Dict[str, Optional[List[str]]]:
        image_tags = {
            image: list(tag_layers.keys()) if tag_layers is not None else None
            for image, tag_layers in self.image_layers.items()
        }
        return image_tags

    @property
    def image_layers(self) -> Dict[str, Optional[Dict[str, List[str]]]]:
        if self._image_layers is None:
            self._image_layers, self._layer_sizes = self._get_image_layers_and_layer_sizes()
        return self._image_layers

    @property
    def primary_image_layers(self) -> Dict[str, Optional[Dict[str, List[str]]]]:
        if self._primary_image_layers is None:
            self._primary_image_layers = self._get_primary_image_layers()
        return self._primary_image_layers

    @property
    def layer_sizes(self) -> Dict[str, int]:
        if self._layer_sizes is None:
            self._image_layers, self._layer_sizes = self._get_image_layers_and_layer_sizes()
        return self._layer_sizes

    @property
    def tag_sizes(self) -> Dict[str, Optional[Dict[str, int]]]:
        if self._tag_sizes is None:
            self._tag_sizes = {
                image: {tag: sum(self.layer_sizes[layer] for layer in layers)
                        for tag, layers in tag_layers.items()} if tag_layers is not None else None
                for image, tag_layers in self.image_layers.items()
            }
        return self._tag_sizes

    @property
    def tag_disk_sizes(self) -> Dict[str, Optional[Dict[str, int]]]:
        if self._tag_disk_sizes is None:
            self._tag_disk_sizes = {
                image: {
                    tag: sum(self.layer_sizes[primary_layer] for primary_layer in primary_layers)
                    for tag, primary_layers in primary_tag_layers.items()
                } if primary_tag_layers is not None else None
                for image, primary_tag_layers in self.primary_image_layers.items()
            }
        return self._tag_disk_sizes

    @property
    def image_sizes(self) -> Dict[str, Optional[int]]:
        if self._image_sizes is None:
            self._image_sizes = {
                image: sum(tag_sizes.values()) if tag_sizes is not None else None
                for image, tag_sizes in self.tag_sizes.items()
            }
        return self._image_sizes

    @property
    def image_disk_sizes(self) -> Dict[str, Optional[int]]:
        if self._image_disk_sizes is None:
            self._image_disk_sizes = {
                image: sum(tag_disk_sizes.values()) if tag_disk_sizes is not None else None
                for image, tag_disk_sizes in self.tag_disk_sizes.items()
            }
        return self._image_disk_sizes

    @property
    def total_size(self) -> int:
        if self._total_size is None:
            self._total_size = cast(int, sum(value for value in self.image_sizes.values() if value is not None))
        return self._total_size

    @property
    def total_disk_size(self) -> int:
        if self._total_disk_size is None:
            self._total_disk_size = cast(
                int, sum(value for value in self.image_disk_sizes.values() if value is not None)
            )
        return self._total_disk_size
