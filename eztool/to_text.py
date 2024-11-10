import argparse

try:
    from ezlib.preproc import preprocess_all
except ImportError:
    import sys
    sys.path.append("../")  # Add parent directory to path
    sys.path.append("./")  # Add current directory to path
    from ezlib.preproc import preprocess_all

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Convert files in a directory to plain text and save them in a mirrored directory structure.",
        epilog="Example usage:\n"
               "  python script.py /path/to/input_dir -v\n"
               "This will process all files in /path/to/input_dir and log details to the console.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "input_dir",
        type=str,
        help="Path to the input directory containing files to be processed."
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed logging in the console."
    )

    args = parser.parse_args()

    # Call preprocess_all with arguments, passing verbose mode status
    preprocess_all(directory=args.input_dir, verbose=args.verbose)

if __name__ == "__main__":
    main()
