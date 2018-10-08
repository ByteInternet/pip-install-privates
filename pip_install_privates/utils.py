def parse_pip_version(version_string):
    return tuple(
        map(
            int,
            version_string.split('.')
        )
    )
