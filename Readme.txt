Semantic Image Search Engine
1. Overview
This project is a powerful desktop application that allows you to find images on your local computer based on their content, not just their filenames. Using state-of-the-art AI (OpenAI's CLIP model), it understands the meaning of an image.

You can provide an image of a dog, and it will find all other pictures of dogs on your hard drive, regardless of the breed, background, or file name.

The application works in two stages:

Indexing: A one-time scan of your specified folders to analyze all your images and create a searchable database (an index).

Searching: A fast, interactive GUI where you can drag-and-drop a query image to find visually similar ones almost instantly.

2. Technology Stack
Language: Python 3.8+

GUI: PyQt5

AI Model: sentence-transformers (using clip-ViT-B-32)

Indexing: faiss-cpu (from Meta AI)

Image Handling: Pillow, numpy

3. Project Structure
The project is organized into several directories to keep the code clean and manageable:

image-search-project/
├── gui/
│   └── main_window.py      # All front-end GUI code (PyQt5)
├── engine/
│   ├── indexer.py          # Logic for scanning files and building the index
│   └── searcher.py         # Logic for loading the index and performing searches
├── data/
│   ├── faiss_index.bin     # (Generated) The saved binary FAISS index file
│   └── image_paths.pkl     # (Generated) The list of image paths for the index
├── main_indexer.py         # Script to START the indexing process
├── main_app.py             # Script to LAUNCH the application
└── requirements.txt        # All necessary Python libraries

4. Installation and Setup
Follow these steps to get the application running.

Step 1: Clone or Download the Project
First, get all the project files onto your computer.

Step 2: Set Up a Virtual Environment (Recommended)
It's best practice to create an isolated environment for the project's dependencies.

# Navigate to the project directory
cd path/to/image-search-project

# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

Step 3: Install Required Libraries
Install all the necessary Python packages using the requirements.txt file.

pip install -r requirements.txt

5. How to Use the Application
Using the application is a two-step process. You must build the index first before you can search.

Step 1: Index Your Images (IMPORTANT: DO THIS FIRST)
You need to tell the application where your photos are located so it can build its search database.

Open your terminal or command prompt.

Make sure your virtual environment is activated.

Run the main_indexer.py script, pointing it to the folder containing your images.

Example:
If all your pictures are in a folder called C:\Users\YourName\Pictures, you would run:

python main_indexer.py --path "C:\Users\YourName\Pictures"

Or for a folder on your D: drive:

python main_indexer.py --path "D:\MyPhotoLibrary"

This process can take a long time, especially if you have thousands of images. You will see a progress bar. Let it run until it completes. It will create the faiss_index.bin and image_paths.pkl files in the data/ directory.

You only need to do this once. If you add many new photos later, you can run it again to update the index.

Step 2: Launch the Search Application
Once the index is built, you can start the visual search application.

In the same terminal, run the main_app.py script:

python main_app.py

The application window will appear.

Drag and drop an image file from your computer onto the designated area, OR click the + button to open a file dialog and select an image.

The application will instantly display the most visually similar images from your indexed collection.

Hover your mouse over any result to see its full file path.