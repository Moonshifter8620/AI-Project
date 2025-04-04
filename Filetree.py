#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
import colorama
from colorama import Fore, Style
import io


def print_file_tree(start_path='.', indent='', max_depth=None, current_depth=0,
                    exclude_dirs=None, exclude_patterns=None, show_hidden=False,
                    colored=True, file=sys.stdout):
    """
    Print the file tree structure starting from the specified path.

    Args:
        start_path (str): The directory to start from
        indent (str): Current indentation string
        max_depth (int): Maximum depth to traverse
        current_depth (int): Current depth in the tree
        exclude_dirs (list): Directories to exclude
        exclude_patterns (list): File/dir patterns to exclude
        show_hidden (bool): Whether to show hidden files/dirs
        colored (bool): Whether to use colored output
        file: The file object to write output to
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_patterns is None:
        exclude_patterns = []

    if max_depth is not None and current_depth > max_depth:
        return

    start_path = Path(start_path)
    if not start_path.exists():
        print(f"Path {start_path} does not exist", file=file)
        return

    # Get the directory name
    directory_name = start_path.name or str(start_path.absolute())

    # Print the root directory differently for the first call
    if current_depth == 0:
        if colored and file == sys.stdout:
            print(f"{Fore.BLUE}{Style.BRIGHT}{directory_name}{Style.RESET_ALL}", file=file)
        else:
            print(directory_name, file=file)

    # Get all items and sort them (dirs first, then files)
    try:
        items = sorted(list(start_path.iterdir()),
                       key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        print(f"{indent}└── [Permission Denied]", file=file)
        return

    # Count items for prefix logic (whether an item is the last in its directory)
    items_count = len(items)

    for idx, item in enumerate(items):
        # Check if we should skip this item
        item_name = item.name

        # Skip hidden files/dirs if not showing hidden
        if not show_hidden and item_name.startswith('.'):
            continue

        # Skip excluded directories
        if item.is_dir() and item_name in exclude_dirs:
            continue

        # Skip excluded patterns
        if any(pattern in item_name for pattern in exclude_patterns):
            continue

        # Determine if this is the last item in the directory
        is_last = idx == items_count - 1

        # Create the prefix for this item
        prefix = "└── " if is_last else "├── "

        # Determine the color for the item (only if outputting to stdout)
        if colored and file == sys.stdout:
            if item.is_dir():
                color_prefix = f"{Fore.BLUE}{Style.BRIGHT}"
            else:
                if item.suffix.lower() in ['.py', '.js', '.java', '.cpp', '.c']:
                    color_prefix = f"{Fore.GREEN}"
                elif item.suffix.lower() in ['.txt', '.md', '.csv', '.json']:
                    color_prefix = f"{Fore.YELLOW}"
                else:
                    color_prefix = f"{Fore.WHITE}"
        else:
            color_prefix = ""

        # Print the item
        if colored and file == sys.stdout:
            print(f"{indent}{prefix}{color_prefix}{item_name}{Style.RESET_ALL}", file=file)
        else:
            print(f"{indent}{prefix}{item_name}", file=file)

        # If it's a directory, recursively print its contents
        if item.is_dir():
            # Calculate the new indent for the next level
            next_indent = indent + ("    " if is_last else "│   ")

            # Recursively print the subdirectory
            print_file_tree(
                item,
                next_indent,
                max_depth,
                current_depth + 1,
                exclude_dirs,
                exclude_patterns,
                show_hidden,
                colored,
                file
            )


def main():
    # Initialize colorama
    colorama.init(autoreset=True)

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Print directory tree structure')
    parser.add_argument('--path', '-p', type=str, default='.',
                        help='The path to start from (default: current directory)')
    parser.add_argument('--max-depth', '-d', type=int, default=None,
                        help='Maximum depth to traverse (default: unlimited)')
    parser.add_argument('--exclude-dirs', '-e', type=str, nargs='+', default=[],
                        help='Directories to exclude (default: none)')
    parser.add_argument('--exclude-patterns', '-x', type=str, nargs='+', default=[],
                        help='Patterns to exclude (default: none)')
    parser.add_argument('--show-hidden', '-a', action='store_true',
                        help='Show hidden files and directories')
    parser.add_argument('--no-color', '-n', action='store_true',
                        help='Disable colored output')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: stdout)')

    args = parser.parse_args()

    # Determine output file
    output_file = args.output or "Filetree.txt"

    # Open the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Print the tree to the file
        print_file_tree(
            start_path=args.path,
            max_depth=args.max_depth,
            exclude_dirs=args.exclude_dirs,
            exclude_patterns=args.exclude_patterns,
            show_hidden=args.show_hidden,
            colored=False,  # No colors in file output
            file=f
        )

    print(f"File tree has been saved to {output_file}")

    # Reset colorama
    colorama.deinit()


if __name__ == "__main__":
    main()