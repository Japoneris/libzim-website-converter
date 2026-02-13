"""
Given a `_site/` with all pages / assets in, create .zim

a webpage should refer to style / assets using `href=/assets/`.
Otherwise, it should handle page relativity itself.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from libzim.writer import Creator

from converter import (
    setup_logging,
    load_config,
    validate_language_code,
    validate_filename,
    sanitize_filename,
    is_pillow_available,
    generate_link_validation_report,
    process_dry_run,
    process_files,
    cleanup_unreferenced,
    resolve_external_dependencies,
)

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert static websites to ZIM archive format for offline viewing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for metadata)
  python3 website_converter.py myblog/_site/

  # Non-interactive mode (all metadata via flags)
  python3 website_converter.py myblog/_site/ --name "My Blog" --title "Personal Blog" \\
    --creator "John Doe" --description "My personal blog" --language eng \\
    --non-interactive

  # Using a configuration file
  python3 website_converter.py myblog/_site/ --config config/example.json
        """
    )

    parser.add_argument("site_path", help="Path to the compiled website directory")
    parser.add_argument("--output_path", default="zim_files", help="Output directory for ZIM file (default: zim_files)")
    parser.add_argument("--icon", default="icons/comment.png", help="Path to ZIM icon (default: icons/comment.png)")

    # Metadata arguments
    parser.add_argument("--name", help="ZIM filename (without .zim extension)")
    parser.add_argument("--title", help="ZIM title metadata")
    parser.add_argument("--creator", help="Creator name")
    parser.add_argument("--publisher", default="You", help="Publisher name (default: You)")
    parser.add_argument("--description", help="Description of the content")
    parser.add_argument("--language", help="ISO 639-3 language code (e.g., eng, fra)")

    # Configuration and verbosity
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode (no prompts, use flags or config)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (DEBUG level)")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output except errors")

    # Phase 3 features
    parser.add_argument("--dry-run", action="store_true", help="Analyze and report without creating ZIM file")
    parser.add_argument("--optimize-images", action="store_true", help="Optimize images (resize/compress) - requires Pillow")
    parser.add_argument("--max-image-width", type=int, default=1920, help="Maximum image width for optimization (default: 1920)")
    parser.add_argument("--image-quality", type=int, default=85, help="JPEG quality for optimization (default: 85)")
    parser.add_argument("--report", action="store_true", help="Generate HTML validation report")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar (useful for logging)")
    parser.add_argument("--resolve-external", action="store_true", help="Download external dependencies (fonts, scripts, CSS) for offline use")
    parser.add_argument("--cleanup", action="store_true", help="Remove unreferenced assets (files not linked from any HTML/CSS) from the ZIM")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Check feature dependencies
    if args.optimize_images and not is_pillow_available():
        logger.warning("--optimize-images requires Pillow. Install with: pip install Pillow")
        logger.warning("Continuing without image optimization.")
        args.optimize_images = False

    if not args.no_progress and not TQDM_AVAILABLE and not args.quiet:
        logger.info("tqdm not available. Install with: pip install tqdm for progress bars.")

    if args.dry_run:
        logger.info("=== DRY RUN MODE - No ZIM file will be created ===")

    # Load configuration file if provided
    config = {}
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)

    # Validate and prepare paths
    load_path = Path(args.site_path)
    if not load_path.exists():
        logger.error(f"Site path does not exist: {load_path}")
        sys.exit(1)
    if not load_path.is_dir():
        logger.error(f"Site path is not a directory: {load_path}")
        sys.exit(1)

    save_path = Path(args.output_path)
    try:
        save_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f"Permission denied creating output directory: {save_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        sys.exit(1)

    # Get metadata (priority: CLI args > config file > interactive prompts > defaults)
    if args.non_interactive:
        # Non-interactive mode: require all metadata
        filename = args.name or config.get('name')
        lang = args.language or config.get('language')
        creator = args.creator or config.get('creator')
        description = args.description or config.get('description')
        title = args.title or config.get('title')
        publisher = args.publisher or config.get('publisher', 'You')

        if not all([filename, lang, creator, description, title]):
            logger.error("Non-interactive mode requires: --name, --language, --creator, --description, --title")
            sys.exit(1)
    else:
        # Interactive mode with defaults from CLI/config
        filename = args.name or config.get('name') or input("ZIM name? \t") or "test"

        if not args.quiet:
            print("For language code, see https://documentation.abes.fr/guide/html/formats/CodesLanguesISO639-3.htm")
        lang = args.language or config.get('language') or input("Language? (eng | fra): \t") or "eng"

        creator = args.creator or config.get('creator') or input("Creator? \t") or "unknown"
        description = args.description or config.get('description') or input("Description? \t") or "This is a test or the field was left empty"
        title = args.title or config.get('title') or input("Title? \t") or "ABC-Test"
        publisher = args.publisher or config.get('publisher', 'You')

    # Validate and sanitize inputs
    if not validate_language_code(lang):
        logger.warning(f"Invalid language code '{lang}'. Using 'eng' as fallback.")
        lang = "eng"

    if not validate_filename(filename):
        logger.warning(f"Invalid filename '{filename}'. Sanitizing...")
        filename = sanitize_filename(filename)
        logger.info(f"Sanitized filename: {filename}")

    current_date = datetime.today().strftime('%Y-%m-%d')

    # Load icon (priority: CLI --icon > config "icon" > default)
    illustration = None
    icon_source = args.icon
    if icon_source == "icons/comment.png" and config.get('icon'):
        # Only use config icon if CLI wasn't explicitly set (still using default)
        icon_source = config['icon']
    icon_path = Path(icon_source)
    try:
        with open(icon_path, "rb") as fp:
            illustration = fp.read()
    except FileNotFoundError:
        logger.warning(f"Icon file not found: {icon_path}. Proceeding without icon.")
    except PermissionError:
        logger.warning(f"Permission denied reading icon: {icon_path}. Proceeding without icon.")
    except Exception as e:
        logger.warning(f"Failed to read icon: {e}. Proceeding without icon.")

    dic_metadata = {
        "creator": creator,
        "description": description,
        "name": filename,
        "publisher": publisher,
        "title": title,
        "language": lang,
        "date": current_date,
    }

    if args.dry_run:
        logger.info("=== Analyzing Website (Dry Run) ===")
    else:
        logger.info("=== Building ZIM Archive ===")

    lst_unknown = []
    lst_missing_index = []
    lst_errors = []
    images_optimized = 0
    bytes_saved = 0

    # Resolve external dependencies if requested
    resolve_external = args.resolve_external or config.get('resolve_external', False)
    url_mapping = None
    if resolve_external:
        url_mapping = resolve_external_dependencies(load_path, logger)
        if url_mapping:
            logger.info(f"Resolved {len(url_mapping)} external dependency URLs")

    # Count files for progress bar (after external deps download so _external/ is included)
    all_files = [f for f in load_path.rglob("*") if f.is_file()]
    total_files = len(all_files)
    logger.info(f"Found {total_files} files to process")

    # Cleanup unreferenced assets if requested
    cleanup = args.cleanup or config.get('cleanup', False)
    removed_count = 0
    if cleanup:
        all_files, removed_count = cleanup_unreferenced(all_files, load_path, logger)
        logger.info(f"After cleanup: {len(all_files)} files to process ({removed_count} removed)")

    if args.dry_run:
        images_optimized, bytes_saved = process_dry_run(
            all_files, load_path, args, lst_unknown, lst_missing_index, lst_errors,
            url_mapping=url_mapping
        )
    else:
        # Normal mode - create ZIM file
        try:
            with Creator(str(save_path / f"{filename}.zim")).config_indexing(True, lang) as creator:
                creator.set_mainpath("index.html")

                # Add illustration if available
                if illustration:
                    try:
                        creator.add_illustration(48, illustration)
                    except Exception as e:
                        logger.warning(f"Failed to add illustration: {e}")

                images_optimized, bytes_saved = process_files(
                    creator, all_files, load_path, args, lst_unknown, lst_missing_index, lst_errors,
                    url_mapping=url_mapping
                )

                use_progress_bar = TQDM_AVAILABLE and not args.no_progress and not args.quiet and not args.verbose
                if not args.quiet and use_progress_bar:
                    print()

                logger.info("=== Adding metadata ===")
                try:
                    for name, value in dic_metadata.items():
                        creator.add_metadata(name.title(), value)
                except Exception as e:
                    logger.error(f"Failed to add metadata: {e}")

                logger.info("=== Compiling ZIM (this may take a while) ===")

        except Exception as e:
            logger.error(f"Failed to create ZIM archive: {e}")
            sys.exit(1)

    # Summary report
    if args.dry_run:
        logger.info("=== Dry Run Analysis Complete ===")
        logger.info(f"Analyzed {total_files} files")
    else:
        logger.info("=== ZIM Archive Created Successfully ===")
        logger.info(f"Output: {save_path / f'{filename}.zim'}")
        logger.info(f"Processed {total_files} files")

    # Cleanup stats
    if cleanup and removed_count > 0:
        logger.info(f"\n=== Cleanup ===")
        logger.info(f"Removed {removed_count} unreferenced assets")

    # Image optimization stats
    if args.optimize_images and images_optimized > 0:
        logger.info(f"\n=== Image Optimization ===")
        logger.info(f"Optimized {images_optimized} images")
        logger.info(f"Saved {bytes_saved / 1024 / 1024:.2f} MB")

    # Validation warnings
    if lst_unknown:
        logger.warning(f"\nMissing mimetypes for {len(set(lst_unknown))} extensions:")
        logger.warning(", ".join(sorted(set(lst_unknown))))

    if lst_missing_index:
        logger.warning(f"\n{len(lst_missing_index)} links ending with / but no index.html found:")
        if args.verbose:
            for warning in lst_missing_index:
                logger.warning(f"  {warning}")
        else:
            logger.warning(f"  (use --verbose to see all warnings)")

    if lst_errors:
        logger.error(f"\n{len(lst_errors)} files failed to process:")
        if args.verbose:
            for error in lst_errors:
                logger.error(f"  {error}")
        else:
            logger.error(f"  (use --verbose to see all errors)")

    # Generate HTML report if requested
    if args.report or args.dry_run:
        logger.info("\n=== Generating Validation Report ===")
        report_path = generate_link_validation_report(lst_missing_index, lst_unknown, lst_errors, save_path)
        if report_path:
            logger.info(f"Report saved to: {report_path}")
        else:
            logger.error("Failed to generate report")
