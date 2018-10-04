import os


def check_integrity(zappa_cli):
    env = zappa_cli.aws_environment_variables or {}

    db_provider = env.get('TC_DRIVER_PROVIDER')
    if db_provider and db_provider != 'sqlite-remote':
        raise ValueError('TC_DRIVER_PROVIDER environment variable must be "sqlite-remote"')

    db_path = env.get('TC_DRIVER_PATH')
    if not db_path:
        raise ValueError('TC_DRIVER_PATH environment variable must be set')

    if not db_path.startswith('s3://'):
        raise ValueError('TC_DRIVER_PATH must be a valid s3:// URL')

    try:
        from terracotta import get_driver, exceptions
    except ImportError as exc:
        raise RuntimeError(
            'Terracotta must be installed before deployment (e.g. via `pip install .`)'
        ) from exc

    os.environ.update(env)
    driver = get_driver(db_path, provider=db_provider)

    # this checks if DB is reachable, readable, and whether its version matches
    try:
        with driver.connect():
            some_dataset = next(iter(driver.get_datasets().keys()))
    except exceptions.InvalidDatabaseError as exc:
        raise RuntimeError(
            'Error while connecting to remote database. Please double-check your AWS environment '
            'variables, and make sure your machine has access to the remote Terracotta database.'
        ) from exc

    # this makes sure that a random raster file is readable
    with driver.connect():
        driver.get_raster_tile(some_dataset)
