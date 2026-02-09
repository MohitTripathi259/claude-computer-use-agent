"""
File Operations Tool.

Provides file system operations restricted to the /workspace directory
for security. The agent can read, write, and list files within this
sandboxed area.
"""

import os
import aiofiles
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Workspace root - all file operations are restricted to this directory
WORKSPACE_ROOT = Path("/workspace")


def _validate_path(path: str) -> Path:
    """
    Validate and resolve a file path.

    Ensures the path is within the workspace directory to prevent
    directory traversal attacks.

    Args:
        path: The path to validate (can be relative or absolute)

    Returns:
        Resolved Path object within workspace

    Raises:
        ValueError: If path escapes workspace
        PermissionError: If path is not allowed
    """
    # Handle both absolute and relative paths
    if path.startswith("/workspace"):
        # Absolute path within workspace
        full_path = Path(path).resolve()
    elif path.startswith("/"):
        # Absolute path outside workspace - prepend workspace
        full_path = (WORKSPACE_ROOT / path.lstrip("/")).resolve()
    else:
        # Relative path
        full_path = (WORKSPACE_ROOT / path).resolve()

    # Security check: ensure path stays within workspace
    try:
        full_path.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise PermissionError(
            f"Access denied: path must be within {WORKSPACE_ROOT}. "
            f"Attempted: {path} -> {full_path}"
        )

    return full_path


async def read_file(path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path: Path to the file (relative to workspace or absolute within workspace)

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If path is outside workspace
    """
    full_path = _validate_path(path)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not full_path.is_file():
        raise ValueError(f"Not a file: {path}")

    logger.info(f"Reading file: {full_path}")

    async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='replace') as f:
        content = await f.read()

    # Warn if file is very large
    if len(content) > 100000:
        logger.warning(f"Large file read: {len(content)} bytes")

    return content


async def write_file(path: str, content: str) -> None:
    """
    Write content to a file.

    Creates parent directories if they don't exist.

    Args:
        path: Path to the file
        content: Content to write

    Raises:
        PermissionError: If path is outside workspace
    """
    full_path = _validate_path(path)

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing file: {full_path} ({len(content)} bytes)")

    async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
        await f.write(content)


async def append_file(path: str, content: str) -> None:
    """
    Append content to a file.

    Args:
        path: Path to the file
        content: Content to append

    Raises:
        PermissionError: If path is outside workspace
    """
    full_path = _validate_path(path)

    # Create parent directories and file if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Appending to file: {full_path} ({len(content)} bytes)")

    async with aiofiles.open(full_path, 'a', encoding='utf-8') as f:
        await f.write(content)


async def list_directory(path: str = "/workspace") -> List[Dict]:
    """
    List contents of a directory.

    Args:
        path: Directory path (defaults to workspace root)

    Returns:
        List of dicts with file info: name, type, size, modified

    Raises:
        FileNotFoundError: If directory doesn't exist
        PermissionError: If path is outside workspace
    """
    full_path = _validate_path(path)

    if not full_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not full_path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    logger.info(f"Listing directory: {full_path}")

    files = []
    for item in sorted(full_path.iterdir()):
        stat = item.stat()
        files.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": stat.st_size if item.is_file() else None,
            "modified": stat.st_mtime
        })

    return files


async def delete_file(path: str) -> None:
    """
    Delete a file.

    Args:
        path: Path to the file to delete

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If path is outside workspace
    """
    full_path = _validate_path(path)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if full_path.is_dir():
        raise ValueError(f"Cannot delete directory with delete_file: {path}")

    logger.info(f"Deleting file: {full_path}")
    full_path.unlink()


async def file_exists(path: str) -> bool:
    """
    Check if a file or directory exists.

    Args:
        path: Path to check

    Returns:
        True if exists, False otherwise
    """
    try:
        full_path = _validate_path(path)
        return full_path.exists()
    except PermissionError:
        return False


async def get_file_info(path: str) -> Dict:
    """
    Get detailed information about a file.

    Args:
        path: Path to the file

    Returns:
        Dict with file information
    """
    full_path = _validate_path(path)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    stat = full_path.stat()

    return {
        "name": full_path.name,
        "path": str(full_path),
        "type": "directory" if full_path.is_dir() else "file",
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "is_readable": os.access(full_path, os.R_OK),
        "is_writable": os.access(full_path, os.W_OK)
    }
