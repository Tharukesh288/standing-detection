import sys
import os
import argparse
from src.utils.logger import setup_logger

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import StandingDetectionSystem

def main():
    logger = setup_logger()
    
    parser = argparse.ArgumentParser(description="AI Standing Detection System")
    parser.add_argument("--source", type=str, default="0", help="Video source: '0' for webcam, or path to mp4 file.")
    parser.add_argument("--output", type=str, default="data/results.json", help="Path to save output JSON data.")
    args = parser.parse_args()

    # Create data directory if needed
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    logger.info("System initializing...")
    
    # Handle numeric webcam source
    source_input = args.source
    if source_input.isdigit():
        source_input = int(source_input)

    try:
        system = StandingDetectionSystem(source=source_input, output_json=args.output)
        logger.info(f"System started with source: {source_input}")
        system.run()
    except Exception as e:
        logger.error(f"System crash: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("System shutdown.")

if __name__ == "__main__":
    main()
