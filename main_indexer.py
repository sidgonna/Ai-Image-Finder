from engine.indexer import main
import sys

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != '--path':
        print("Usage: python main_indexer.py --path <image_folder> [--output <output_folder>]")
        sys.exit(1)
    image_folder = sys.argv[2]
    output_folder = "data"
    if len(sys.argv) > 4 and sys.argv[3] == '--output':
        output_folder = sys.argv[4]
    main(image_folder, output_folder)
