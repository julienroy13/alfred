import logging
import sys
from math import floor, log10
import re
from tqdm import tqdm

from alfred.utils.config import config_to_str
from alfred.utils.directory_tree import DirectoryTree, get_root, get_storage_dirs_across_tasks


def create_logger(name, loglevel, logfile=None, streamHandle=True):
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - {} - %(message)s'.format(name),
                                  datefmt='%d/%m/%Y %H:%M:%S', )

    handlers = []
    if logfile is not None:
        handlers.append(logging.FileHandler(logfile, mode='a'))
    if streamHandle:
        handlers.append(logging.StreamHandler(stream=sys.stdout))

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def create_new_filehandler(logger_name, logfile):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - {} - %(message)s'.format(logger_name),
                                  datefmt='%d/%m/%Y %H:%M:%S', )

    file_handler = logging.FileHandler(logfile, mode='a')
    file_handler.setFormatter(formatter)

    return file_handler


def round_to_two(x):
    return round(x, -int(floor(log10(abs(x))) - 1))


def keep_two_signif_digits(x):
    return round(x, -int(floor(log10(abs(x))) - 1))


def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def create_management_objects(dir_tree, logger, pbar, config):
    # Creates directory tres

    if dir_tree is None:
        dir_tree = DirectoryTree(alg_name=config.alg_name,
                                 task_name=config.task_name,
                                 desc=config.desc,
                                 seed=config.seed,
                                 root=config.root_dir)

        dir_tree.create_directories()

    # Creates logger and prints config

    if logger is None:
        logger = create_logger('MASTER', config.log_level, dir_tree.seed_dir / 'logger.out')
    logger.debug(config_to_str(config))

    # Creates a progress-bar

    if pbar == "default_pbar":
        pbar = tqdm()

    if pbar is not None:
        pbar.n = 0
        pbar.desc += f'{dir_tree.storage_dir.name}/{dir_tree.experiment_dir.name}/{dir_tree.seed_dir.name}'
        pbar.total = config.max_episodes

    return dir_tree, logger, pbar


def check_params_defined_twice(keys):
    counted_keys = {key: keys.count(key) for key in keys}
    for key in counted_keys.keys():
        if counted_keys[key] > 1:
            raise ValueError(f'Parameter "{key}" appears {counted_keys[key]} times in the schedule.')


def select_storage_dirs(from_file, storage_name, over_tasks, root_dir):
    if from_file is not None:
        assert storage_name is None, "If launching --from_file, no storage_name should be provided"
        assert over_tasks is False, "--over_tasks is not allowed when running --from_file"

    if storage_name is not None or over_tasks is not False:
        assert from_file is None, "Cannot launch --from_file if --storage_name or --over_tasks is defined"

    if from_file is not None:
        with open(from_file, "r") as f:
            storage_names = f.readlines()
        storage_names = [sto_name.strip('\n') for sto_name in storage_names]

        storage_dirs = [get_root(root_dir) / sto_name for sto_name in storage_names]

    elif storage_name is not None:

        storage_dir = get_root(root_dir) / storage_name

        if over_tasks:
            storage_dirs = get_storage_dirs_across_tasks(storage_dir, root_dir=root_dir)
        else:
            storage_dirs = [storage_dir]

    else:
        raise NotImplementedError("storage_dirs to operate over must be specified either by --from_file or --storage_name")

    return storage_dirs
