# Example scripts

- [registry_analyze.py](registry_analyze.py) - list all images and tags, create json cache as result
- [create_lstags.py](create_lstags.py) - load cached json, and create [lstags] config

[lstags]: https://github.com/ivanilves/lstags

```
cp cred.example.py cred.prod.py
./registry_analyze.py cred.prod.py
./create_lstags.py cred.prod.py  > lstags.yml
```
