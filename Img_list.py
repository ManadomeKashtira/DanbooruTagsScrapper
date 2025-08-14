from pathlib import Path
from typing import Optional, Set
import argparse


def get_common_image_extensions() -> Set[str]:
    """
    Return a set of common image file extensions (lowercase).
    """
    return {
        # JPEG formats
        ".jpg", ".jpeg", ".jpe", ".jfif",
        # PNG
        ".png",
        # GIF
        ".gif",
        # Bitmap
        ".bmp", ".dib",
        # TIFF
        ".tiff", ".tif",
        # WebP
        ".webp",
        # SVG
        ".svg", ".svgz",
        # RAW formats
        ".raw", ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2",
        # Other formats
        ".ico", ".icns",
        ".psd",  
        ".ai",   
        ".eps",  
        ".pdf",  
        ".heic", ".heif",  
        ".avif",  
        ".jxl",   
    }


def collect_image_files(
    directory: Path, 
    extensions: Optional[Set[str]] = None,
    recursive: bool = False,
    include_hidden: bool = False
) -> list[str]:
    """
    Collect image filenames from the specified directory.
    
    Args:
        directory: Directory to search in
        extensions: Set of extensions to look for (None = all common image formats)
        recursive: Whether to search subdirectories
        include_hidden: Whether to include hidden files (starting with .)
    
    Returns:
        Sorted list of image filenames
    """
    if extensions is None:
        extensions = get_common_image_extensions()
    
    # Convert extensions to lowercase for case-insensitive matching
    extensions = {ext.lower() for ext in extensions}
    
    image_files = []
    
    # Choose iteration method based on recursive flag
    if recursive:
        pattern = "**/*"
        entries = directory.glob(pattern)
    else:
        entries = directory.iterdir()
    
    for entry in entries:
        if not entry.is_file():
            continue
            
        # Skip hidden files unless explicitly included
        if not include_hidden and entry.name.startswith('.'):
            continue
            
        # Check if file extension matches
        if entry.suffix.lower() in extensions:
            image_files.append(entry.name)
    
    # Sort case-insensitively
    image_files.sort(key=str.casefold)
    return image_files


def write_files_to_output(
    file_names: list[str], 
    output_file: Path,
    include_stats: bool = True
) -> None:
    """
    Write filenames to output file with optional statistics.
    
    Args:
        file_names: List of filenames to write
        output_file: Path to output file
        include_stats: Whether to include file count and extension stats
    """
    content = []
    
    if include_stats:
        content.append(f"# Image Files Found: {len(file_names)}")
        content.append(f"# Founded in: {Path(__file__).name}")
        content.append("")
        
        # Extension statistics
        if file_names:
            ext_counts = {}
            for name in file_names:
                ext = Path(name).suffix.lower()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            
            content.append("# Extension Summary:")
            for ext, count in sorted(ext_counts.items()):
                content.append(f"# {ext}: {count} files")
            content.append("")
    
    # Add filenames
    content.extend(file_names)
    
    # Write to file
    output_file.write_text("\n".join(content), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect and list image files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # List all images in current directory
  %(prog)s -d /path/to/images       # List images in specific directory
  %(prog)s -r                       # Include subdirectories
  %(prog)s -e .jpg .png             # Only look for specific extensions
  %(prog)s -o my_images.txt         # Custom output filename
        """
    )
    
    parser.add_argument(
        "-d", "--directory",
        type=Path,
        default=Path("."),
        help="Directory to search (default: current directory)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("image_files.txt"),
        help="Output file name (default: image_files.txt)"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search subdirectories recursively"
    )
    
    parser.add_argument(
        "-e", "--extensions",
        nargs="+",
        help="Specific extensions to search for (e.g., .jpg .png)"
    )
    
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files (starting with .)"
    )
    
    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Don't include statistics in output file"
    )
    
    parser.add_argument(
        "--list-extensions",
        action="store_true",
        help="List all supported image extensions and exit"
    )
    
    args = parser.parse_args()
    
    # List supported extensions if requested
    if args.list_extensions:
        extensions = sorted(get_common_image_extensions())
        print("Supported image extensions:")
        for ext in extensions:
            print(f"  {ext}")
        return
    
    # Validate directory
    if not args.directory.exists():
        print(f"Error: Directory '{args.directory}' does not exist")
        return
    
    if not args.directory.is_dir():
        print(f"Error: '{args.directory}' is not a directory")
        return
    
    # Parse extensions if provided
    extensions = None
    if args.extensions:
        extensions = set()
        for ext in args.extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            extensions.add(ext.lower())
    
    # Collect image files
    try:
        image_files = collect_image_files(
            args.directory,
            extensions=extensions,
            recursive=args.recursive,
            include_hidden=args.include_hidden
        )
        
        # Write results
        write_files_to_output(
            image_files,
            args.output,
            include_stats=not args.no_stats
        )
        
        # Print summary
        search_type = "recursive" if args.recursive else "non-recursive"
        print(f"Found {len(image_files)} image file(s) in '{args.directory}' ({search_type})")
        print(f"Results written to: {args.output}")
        
        if extensions:
            ext_list = ", ".join(sorted(extensions))
            print(f"Searched for extensions: {ext_list}")
        
    except PermissionError:
        print(f"Error: Permission denied accessing '{args.directory}'")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()