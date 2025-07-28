# PDF Extraction - Challenge 1A

This project extracts the **title** and **outline** (headings) from PDF documents using Python and [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/). It works on local systems and inside Docker containers for better portability.

## Project Structure

```
Challange_1a/
├── simple_pdf_extractor.py      # Main PDF processing script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── sample_dataset/pdfs/        # Input PDF files
├── outputs/                     # Generated JSON outputs
```

## Features

* Extracts the main title from a PDF
* Detects hierarchical outlines (H1–H4) using font size, boldness, and content structure
* Handles different document complexities (simple, medium, complex)
* Can be run locally or in a Docker container

##  Run Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Place PDF files in:

   ```
   sample_dataset/pdfs/
   ```

3. Run the script:

   ```bash
   python simple_pdf_extractor.py
   ```

4. Outputs will be saved in:

   ```
   outputs/
   ```

## Run with Docker

1. Build the Docker image:

   ```bash
   docker build -t pdf_extraction_challange_1a .
   ```

2. Run the Docker container:

   ```bash
   docker run --rm -v $(pwd)/sample_dataset/pdfs:/Challange_1a/sample_dataset/pdfs -v $(pwd)/outputs:/Challange_1a/outputs pdf_extraction_challange_1a
   ```

   > This mounts your local input and output folders into the container.

3. (Optional) Push to DockerHub:

   ```bash
   docker tag pdf_extraction_challange_1a venugopal376/pdf_extraction_challange_1a
   docker push venugopal376/pdf_extraction_challange_1a
   ```

## 🛆 Requirements

* Python 3.11 (or use Docker to skip installation)
* `PyMuPDF==1.23.14`

## 📄 Output Format

Each processed PDF will generate a `.json` file like:

```json
{
  "title": "Example PDF Title",
  "outline": [
    {"level": "H1", "text": "Introduction", "page": 1},
    {"level": "H2", "text": "Background", "page": 2}
  ]
}
```

## ⚙️ Customization

To change the input/output folders, modify the function call in:

```python
process_all_pdfs_individually("sample_dataset/pdfs", "outputs")
```

in the `simple_pdf_extractor.py` file.