# Versioning

## When to update
In general, we keep the version number in sync with the API version number and use [Semantic Versioning](https://semver.org/).

## How to update

## Command Summary

``` shell
git tag
git tag -a NEW_VERSION_TAG -m "VERSION_NAME"
git push --tags
git push --delete origin PREVIOUS_VERSION_TAG
```

> **Note**: The version tag will not be reflected on the API frontend until the image is rebuilt and served on AWS, because that is when it pulls in the tag data from GitHub.


### Checking the version

```shell
git tag
```

This should output something similar to:

> v2.1.27

### Updating the tag

Run the following command from the root directory of the project:

```shell
git tag -a v2.1.28 -m "MVP Release"
```


### Pushing the version

```shell
git push --tags
```

### Removing the old tag

Since we only need one version tag, we need will remove the old tag by using:

```shell
git push --delete origin v2.1.27
```



## Other notes

### Versioning History

(2.0.4)
2.0.0

Branches --> Image:
- main (v2.0.4) --> metro-api-v2:2.0
- dev  (v2.0.5) --> metro-api-v2:2.0-dev
  dev  (v2.0.50)

"Early Access" Release: 2.1.0 (2.0.50)

- main (v2.1.0) --> metro-api-v2:2.1
- dev  (v2.1.1) --> metro-api-v2:2.1-dev

"Full" Release: 2.2.0 (2.1.50)


-----------------

MVP Release: 2.0.0
- main (v2.0.0) --> metro-api-v2:2.0

"Early Access" Release: 2.1.0
- dev  (v2.1.0) --> metro-api-v2:2.1-dev
  dev  (v2.1.0)
- main (v2.1.0) --> metro-api-v2:2.1
  hotfix (v2.1.1)

"Full" Release: 2.2.0
- dev  (v2.2.0) --> metro-api-v2:2.2-dev
- main (v2.2.0) --> metro-api-v2:2.2