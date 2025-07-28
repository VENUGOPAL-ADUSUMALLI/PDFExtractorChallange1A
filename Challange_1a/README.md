# PDF Extraction - Challenge 1A

This project extracts the **title** and **outline** (headings) from PDF documents using Python and [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/). It works both on local systems and inside Docker containers for better portability.

---

##  Approach

The solution analyzes the PDF structure to:

* Extract the **document title** using common formatting patterns (e.g., largest font text near the top).
* Detect hierarchical **headings (H1–H4)** based on font size, boldness, indentation, and structural layout.

The logic handles different levels of document complexity (simple, medium, complex) by adaptively evaluating font properties.

---

##  Project Structure

```
Challange_1a/
├── simple_pdf_extractor.py      # Main PDF processing script
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── sample_dataset/pdfs/        # Input PDF files
├── outputs/                     # Generated JSON outputs
```

---

##  Libraries & Tools Used

* **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** for parsing PDF structure and text attributes
* **Python 3.11**
* **Docker** for containerization and reproducibility

---

## Run Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Place your PDF files in the following folder:

   ```bash
   sample_dataset/pdfs/
   ```

3. Run the script:

   ```bash
   python simple_pdf_extractor.py
   ```

4. Outputs will be saved to:

   ```bash
   outputs/
   ```

---

##  Run with Docker

1. Build the Docker image:

   ```bash
   docker build -t pdf_extraction_challange_1a .
   ```

2. Run the Docker container:

   ```bash
   docker run --rm \
     -v $(pwd)/sample_dataset/pdfs:/Challange_1a/sample_dataset/pdfs \
     -v $(pwd)/outputs:/Challange_1a/outputs \
     pdf_extraction_challange_1a
   ```

> This mounts your local input and output folders into the container for data access.

3. (Optional) Push to DockerHub:

   ```bash
   docker tag pdf_extraction_challange_1a venugopal376/pdf_extraction_challange_1a
   docker push venugopal376/pdf_extraction_challange_1a
   ```

---

## Output Format

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

---

## Customization

To change the input/output folders, modify the function call in `simple_pdf_extractor.py`:

```python
process_all_pdfs_individually("sample_dataset/pdfs", "outputs")
```

Update the paths as needed to support alternate directory structures.

---

##  Requirements

* Python 3.11+
* `PyMuPDF==1.23.14`
* (Or simply use Docker to skip local setup)

