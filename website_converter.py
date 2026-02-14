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
from types import SimpleNamespace

from libzim.writer import Creator

from converter import (
    setup_logging,
    load_config,
    validate_config,
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
  # Basic usage — all settings come from the config file
  python3 website_converter.py config/my-site.json

  # Dry-run to analyze without creating a ZIM
  python3 website_converter.py config/my-site.json --dry-run

  # Verbose output
  python3 website_converter.py config/my-site.json --verbose

Create a config file interactively:
  python3 create_config.py
        """
    )

    parser.add_argument("config_file", help="Path to JSON configuration file")

    # Runtime flags only — everything else comes from the config
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (DEBUG level)")
    parser.add_argument("--quiet", action="store_true", help="Suppress all output except errors")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and report without creating ZIM file")
    parser.add_argument("--report", action="store_true", help="Generate HTML validation report")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar (useful for logging)")

    cli_args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=cli_args.verbose, quiet=cli_args.quiet)

    # Load and validate config
    logger.info(f"Loading configuration from {cli_args.config_file}")
    config = load_config(cli_args.config_file)
    config = validate_config(config)

    # Build a unified args namespace for file_processor compatibility
    args = SimpleNamespace(
        verbose=cli_args.verbose,
        quiet=cli_args.quiet,
        dry_run=cli_args.dry_run,
        report=cli_args.report,
        no_progress=cli_args.no_progress,
        optimize_images=config["optimize_images"],
        max_image_width=config["max_image_width"],
        image_quality=config["image_quality"],
    )

    # Check feature dependencies
    if args.optimize_images and not is_pillow_available():
        logger.warning("optimize_images requires Pillow. Install with: pip install Pillow")
        logger.warning("Continuing without image optimization.")
        args.optimize_images = False

    if not args.no_progress and not TQDM_AVAILABLE and not args.quiet:
        logger.info("tqdm not available. Install with: pip install tqdm for progress bars.")

    if args.dry_run:
        logger.info("=== DRY RUN MODE - No ZIM file will be created ===")

    # Validate and prepare paths
    load_path = Path(config["site_path"])
    if not load_path.exists():
        logger.error(f"Site path does not exist: {load_path}")
        sys.exit(1)
    if not load_path.is_dir():
        logger.error(f"Site path is not a directory: {load_path}")
        sys.exit(1)

    save_path = Path(config["output_path"])
    try:
        save_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f"Permission denied creating output directory: {save_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        sys.exit(1)

    # Validate and sanitize metadata
    filename = config["name"]
    lang = config["language"]
    creator = config["creator"]
    description = config["description"]
    title = config["title"]
    publisher = config["publisher"]

    if not validate_language_code(lang):
        logger.warning(f"Invalid language code '{lang}'. Using 'eng' as fallback.")
        lang = "eng"

    if not validate_filename(filename):
        logger.warning(f"Invalid filename '{filename}'. Sanitizing...")
        filename = sanitize_filename(filename)
        logger.info(f"Sanitized filename: {filename}")

    current_date = datetime.today().strftime('%Y-%m-%d')

    # Load icon
    illustration = None
    icon_path = Path(config["icon"])
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
    resolve_external = config.get('resolve_external', False)
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
    cleanup = config.get('cleanup', False)
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
