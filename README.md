# dir_tree_builder

dir_tree_builder is a Python module and CLI tool for recursively building a directory tree and outputting it as JSON. It supports file metadata, nested directories, empty directories, and optional human-readable file sizes and timestamps.

---

## Features

- Recursively traverse directories to any depth (or unlimited with -1)  
- Represent files with metadata (size and last modification time)  
- Represent directories as nested dictionaries  
- Include empty directories explicitly  
- Optionally format sizes and timestamps in human-readable form  
- Handles permission errors gracefully  
- Safe to import as a module; logging is optional and configurable  
- Python 3.8+ compatible  
- No external dependencies, uses only standard library  

---

## Installation

Clone or download the repository. No pip installation is required:

```
git clone https://github.com/abbas-jafri-aj/dir_tree_builder.git
cd dir_tree_builder
```

---

## Usage

### As a script

```
python dir_tree_builder.py /home/user/project [--depth N] [--human-readable] [--logfile FILE]
```

- `path` : Directory or file to inspect
- `--depth N` : Maximum recursion depth (default: 3, -1 for unlimited)  
- `--human-readable` : Display human-readable sizes and timestamps  
- `--logfile FILE` : Optional log file path  

Example:

```
$ python dir_tree_builder.py /usr/local --depth 2 --human-readable
09:54:30 [INFO] Building directory tree for /usr/local (depth=2, human_readable=True)
{
    "bin": {
        "start-systemd": {
            "size": "3.7 KB",
            "modified_time": "2023-05-02 18:50"
        },
        "update.sh": {
            "size": "5.1 KB",
            "modified_time": "2023-05-02 18:50"
        },
        "upgrade.sh": {
            "size": "5.1 KB",
            "modified_time": "2023-05-02 18:50"
        },
        "wslsystemctl": {
            "size": "284.6 KB",
            "modified_time": "2023-05-02 18:50"
        }
    },
    "etc": {},
    "games": {},
    "include": {},
    "lib": {},
    "lib64": {
        "bpf": {}
    },
    "libexec": {},
    "sbin": {},
    "share": {
        "applications": {},
        "info": {},
        "man": {}
    },
    "src": {}
}
```

### As a module

Import and use in your Python code:

```
from dir_tree_builder import get_dir_tree, dir_tree_to_json

tree = get_dir_tree("/home/user/project", depth=2, human_readable=True)
print(dir_tree_to_json(tree))
```

Optional logging can be passed:

```
import logging
from dir_tree_builder import get_dir_tree, setup_logger

logger = setup_logger("tree.log")
tree = get_dir_tree("/home/user/project", depth=2, human_readable=True, logger=logger)
```

---

## Logging

- By default, the module does not output logs when imported.  
- Use the optional `logger` parameter in `get_dir_tree` or `get_file_info` to enable logging.  
- When running as a script, use `--logfile` to write logs to a file.  

---

## License

MIT License
