import os
import sys
import argparse
from pathlib import Path


def generate_tree(root_dir, extensions, output_file, exclude_dirs, show_all, dirs_only):
    root_path = Path(root_dir).resolve()

    # Absolute path of this script, to avoid listing itself
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        script_path = None

    output_path = Path(output_file).resolve() if output_file else None

    # Baseline junk directories that are always ignored
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv',
                   'env', '.idea', '.vscode', 'flashenv', 'dist', 'build', 'target'}
    if exclude_dirs:
        ignore_dirs.update(exclude_dirs)

    # Ensure extensions start with a dot
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]

    def matches(name):
        return show_all or any(name.endswith(ext) for ext in extensions)

    def scan(path):
        """Return (dirs, files) as sorted lists of os.DirEntry, filtered."""
        dirs, files = [], []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in ignore_dirs:
                            dirs.append(entry)
                    elif not dirs_only and entry.is_file(follow_symlinks=False):
                        resolved = Path(entry.path).resolve()
                        if resolved == output_path or resolved == script_path:
                            continue
                        if matches(entry.name):
                            files.append(entry)
        except (PermissionError, OSError):
            pass
        dirs.sort(key=lambda e: e.name.lower())
        files.sort(key=lambda e: e.name.lower())
        return dirs, files

    # In default mode, prune directories that contain no matching files
    # anywhere in their subtree. Keep all dirs in --all / --dirs-only modes.
    prune = not show_all and not dirs_only

    def build(path):
        dirs, files = scan(path)
        nodes = []
        for d in dirs:
            children = build(d.path)
            if children or not prune:
                nodes.append((d.name, True, children))
        for f in files:
            nodes.append((f.name, False, None))
        return nodes

    def render(nodes, prefix=""):
        lines = []
        last_i = len(nodes) - 1
        for i, (name, is_dir, children) in enumerate(nodes):
            last = i == last_i
            connector = "└── " if last else "├── "
            label = name + ("/" if is_dir else "")
            lines.append(prefix + connector + label)
            if is_dir:
                extension = "    " if last else "│   "
                lines.extend(render(children, prefix + extension))
        return lines

    tree = "\n".join([root_path.name + "/"] + render(build(root_path)))
    print(tree)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tree + "\n")
        print(f"\n[tree written to '{output_file}']", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print the nested directory tree (extension-filtered) for AI dev context.")

    parser.add_argument("-d", "--directory", type=str, default=".",
                        help="Root directory to scan (default: current directory)")

    parser.add_argument("-e", "--extensions", type=str, nargs="+",
                        default=["py", "md", "txt", "json", "csv", "sh", "yml", "yaml","properties","java","xml","ini","bat","cfg","conf","toml",
                                 "gradle","js","ts","jsx","tsx","html","css","scss","less","php","rb","pl","go","rs","iml","gradle.kts","dockerfile",
                                 "makefile","cmake","cmake.in","cmake.in.template","pro"],
                        help="File extensions to include")

    parser.add_argument("-x", "--exclude-dirs", type=str, nargs="+", default=["__MACOSX"],
                        help="Additional directories to exclude (default: __MACOSX)")

    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Optional output file; prints to stdout if omitted")

    parser.add_argument("-a", "--all", action="store_true",
                        help="Include all files regardless of extension")

    parser.add_argument("--dirs-only", action="store_true",
                        help="Show directories only (no files)")

    args = parser.parse_args()
    generate_tree(args.directory, args.extensions, args.output,
                  args.exclude_dirs, args.all, args.dirs_only)