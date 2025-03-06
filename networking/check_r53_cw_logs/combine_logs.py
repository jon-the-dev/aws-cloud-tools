#!/usr/bin/env python3
# import os
import argparse
import logging
from pathlib import Path


def combine_logs(log_folder: str, output: str, verbose: bool):
    """
    Combine all log files in the provided folder, sort the lines, and write the output.

    Parameters:
      log_folder: Path to the folder containing log files.
      output: Path to the output file.
      verbose: Enable verbose logging.
    """
    folder_path = Path(log_folder).resolve()
    if not folder_path.is_dir():
        logging.error(f"Provided path '{folder_path}' is not a directory.")
        return

    # Gather all files in the folder (ignoring subdirectories)
    files = [p for p in folder_path.iterdir() if p.is_file()]
    logging.info(f"Found {len(files)} file(s) in '{folder_path}'.")

    combined_lines = []
    for file in files:
        logging.info(f"Reading file: {file.name}")
        try:
            with file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                combined_lines.extend(lines)
        except Exception as e:
            logging.error(f"Error reading {file}: {e}")

    logging.info(f"Total lines read: {len(combined_lines)}")

    # Sort the lines (assumes logs are in a format that sorts correctly)
    sorted_lines = sorted(combined_lines)
    logging.info("Sorting complete.")

    # Write the sorted lines to the output file
    try:
        with open(output, "w", encoding="utf-8") as out_file:
            out_file.writelines(sorted_lines)
        logging.info(f"Combined log written to '{output}'.")
    except Exception as e:
        logging.error(f"Error writing to {output}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Combine and sort all log files in a folder into one file outside the folder."
    )
    parser.add_argument("log_folder", help="Path to the folder containing log files")
    parser.add_argument(
        "--output",
        help="Path for the combined output file. Defaults to the parent directory of the log folder as 'combined.log'",
        default=None,
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    # If no output file is provided, default to 'combined.log' in the parent directory of the log folder.
    if args.output:
        output_file = args.output
    else:
        folder_path = Path(args.log_folder).resolve()
        output_file = str(folder_path.parent / "combined.log")

    combine_logs(args.log_folder, output_file, args.verbose)


if __name__ == "__main__":
    main()
