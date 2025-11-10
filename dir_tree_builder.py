#!/usr/bin/env python3
"""
dir_tree_builder.py

Recursively build and print a directory tree in JSON format.

This script:
  • Traverses directories up to a specified depth (or unlimited if depth = -1)
  • Represents files as dicts containing metadata
  • Represents directories as nested dicts
  • Optionally shows file size and modified time in human-readable form
  • Handles permission errors gracefully
  • Uses structured logging for debug and error output

Example invocation:
    python build_dir_tree.py "/path/to/dir" --depth 2 --human-readable --logfile tree.log
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Union, Optional, Any

# ---------------------------------------------------------------------------
# Type aliases: FileMetadata and DirTree, especially created for this module
# ---------------------------------------------------------------------------

# Type alias for file metadata
# FileMetadata is a dictionary describing a single file’s properties:
# - Keys are strings (like "size" or "modified_time")
# - Values are int (raw bytes or timestamp) or str (human-readable)
FileMetadata = Dict[str, Union[int, str]]

# Type alias for recursive directory structure
# DirTree defines the nested dictionary shape returned by build_dir_tree().
# Each key is a filename or directory name (str)
# Each value (Union[...]) can be one of:
#   - FileMetadata -> file with metadata (size, modified time)
#   - "DirTree" -> represents nested directory of type "DirTree" (recursive)
#   - {} -> empty directory explicitly included
DirTree = Dict[str, Union[FileMetadata, "DirTree"]]

# Example illustrating all DirTree cases:
#
# tree = {
#     # File with metadata (leaf node)
#     "README.md": {"size": 512, "modified_time": "2025-11-10 22:30"},
#
#     # Directory containing files and nested directories (creates a DirTree subtree)
#     "src": {
#         # File with metadata (leaf node)
#         "main.py": {"size": 2048, "modified_time": "2025-11-10 23:01"},
#
#         # Nested directory (creates another DirTree subtree)
#         "utils": {
#             # File with metadata (leaf node)
#             "helpers.py": {"size": 1024, "modified_time": "2025-11-10 22:55"},
#             
#             # Empty directory explicitly included (leaf DirTree subtree)
#             "empty_dir": {}
#         }
#     },
#
#     # Completely empty top-level directory (leaf DirTree subtree)
#     "docs": {}
# }

# ---------------------------------------------------------------------------
# Module-level logger (does nothing unless configured by the caller)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # Prevent "No handler found" warnings

def setup_logger(logfile: Optional[str] = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Configure and return a logger.
    Logs to console by default, and to file if logfile is provided.
    Only used when running the script directly.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.propagate = False  # Avoid duplicate logs if imported

    # Formatter for console/file
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format (e.g., 1.2 KB, 3.4 MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size_bytes /= 1024.0
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
    return f"{size_bytes:.1f} PB"

def human_readable_time(timestamp: float) -> str:
    """Convert UNIX timestamp to human-readable datetime string."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def get_file_info(
    path: Union[str, Path],
    human_readable: bool = False,
    logger: Optional[logging.Logger] = None
) -> FileMetadata:
    """
    Get metadata for a single file.

    Returns a dictionary containing:
        - "size": file size in bytes or human-readable string
        - "modified_time": last modification time as timestamp or human-readable string

    Parameters:
        path (Path): The file path to inspect.
        human_readable (bool): If True, returns size and modified_time in human-readable format.
        logger (Optional[Logger]): Optional logger for warnings; defaults to module logger.
    
    Returns:
        FileMetadata: Dictionary describing the file's size and modified time.

    Raises TypeError if input types are invalid.

    Example:
        get_file_info(Path("README.md"), human_readable=True)
        -> {"size": "512 B", "modified_time": "2025-11-10 22:30"}
    """
    
    logger = logger or logging.getLogger(__name__)

    # Validate input type
    if isinstance(path, str):
        path = Path(path)
    elif not isinstance(path, Path):
        raise TypeError(f"'path' must be str or Path, got {type(path)}")

    if not path.exists():
        logger.warning(f"File does not exist: {path}")
        return {}

    try:
        stats = path.stat()
        size = human_readable_size(stats.st_size) if human_readable else stats.st_size
        modified_time = human_readable_time(stats.st_mtime) if human_readable else stats.st_mtime
        return {"size": size, "modified_time": modified_time}
    except (OSError, PermissionError) as e:
        logger.warning(f"Cannot access file info for: {path} ({e})")
        return {}

def get_dir_tree(
    path: Union[str, Path],
    depth: int = 3,
    human_readable: bool = False,
    logger: Optional[logging.Logger] = None
) -> DirTree:
    """
    Recursively build a nested dictionary representing the directory tree.

    Files are represented as FileMetadata dictionaries.
    Empty directories are explicitly included as {}.
    Nested directories are represented recursively as DirTree.

    Parameters:
        path (Path): Directory or file to traverse.
        depth (int): Maximum recursion depth (-1 for unlimited).
        human_readable (bool): If True, file sizes and modified times are human-readable.
        logger (Optional[Logger]): Optional logger; defaults to module logger.

    Returns:
        DirTree: Nested dictionary representing the directory structure.

    Raises:
       TypeError, ValueError, FileNotFoundError for invalid input
    
    Example:
        tree = get_dir_tree(Path("/project"), depth=2, human_readable=True)
        Produces a DirTree similar to:

        {
            "README.md": {"size": "512 B", "modified_time": "2025-11-10 22:30"},
            "src": {
                "main.py": {"size": "2048 B", "modified_time": "2025-11-10 23:01"},
                "utils": {
                    "helpers.py": {"size": "1024 B", "modified_time": "2025-11-10 22:55"},
                    "empty_dir": {}
                }
            },
            "docs": {}
        }
    """
    
    logger = logger or logging.getLogger(__name__)

    # Validate input types
    if isinstance(path, str):
        path = Path(path)
    elif not isinstance(path, Path):
        raise TypeError(f"'path' must be str or Path, got {type(path)}")

    if not isinstance(depth, int):
        raise TypeError(f"'depth' must be int, got {type(depth)}")
    if depth < -1:
        raise ValueError(f"'depth' must be -1 (unlimited) or >=0, got {depth}")

    if not isinstance(human_readable, bool):
        raise TypeError(f"'human_readable' must be bool, got {type(human_readable)}")

    if logger is not None and not isinstance(logger, logging.Logger):
        raise TypeError(f"'logger' must be logging.Logger or None, got {type(logger)}")

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    # Dict of type DirTree, type alias defined above
    tree: DirTree = {}

    # Base case: single file
    if path.is_file():
        return {path.name: get_file_info(path, human_readable, logger)}

    # Stop recursion at depth 0
    if depth == 0:
        return {}

    try:
        entries = sorted(path.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        logger.warning(f"Permission denied: {path}")
        return {}

    for entry in entries:
        if entry.is_dir():
            subtree = get_dir_tree(
                entry, depth - 1 if depth > 0 else -1, human_readable, logger
            )
            tree[entry.name] = subtree or {}  # Include empty dirs explicitly
        elif entry.is_file():
            tree[entry.name] = get_file_info(entry, human_readable, logger)
        else:
            logger.debug(f"Skipping non-file, non-dir entry: {entry}")

    return tree

# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def dir_tree_to_json(tree: DirTree) -> str:
    """Convert directory tree dict to pretty-printed JSON string."""
    return json.dumps(tree, indent=4, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and print a directory tree in JSON format.")
    parser.add_argument("path", help="Path to the directory or file to inspect.")
    parser.add_argument("--depth", type=int, default=3,
                        help="Recursion depth (-1 for unlimited). Default: 3")
    parser.add_argument("--human-readable", action="store_true",
                        help="Show human-readable sizes and timestamps.")
    parser.add_argument("--logfile", type=str, default=None, help="Optional log file path.")
    args = parser.parse_args()

    logger = setup_logger(args.logfile)
    logger.info(f"Building directory tree for {args.path} "
                f"(depth={args.depth}, human_readable={args.human_readable})")

    try:
        tree = get_dir_tree(args.path, args.depth, args.human_readable, logger)
        print(dir_tree_to_json(tree))
        logger.info("Directory tree successfully generated.")
    except Exception as e:
        logger.exception(f"Error while building directory tree: {e}")
        sys.exit(1)
