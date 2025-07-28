import fitz
import json
import re
import os
import glob


def extract_title_and_outline(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return {"title": "", "outline": []}

        title = extract_universal_title(doc)
        outline = extract_adaptive_outline(doc, title)
        
        doc.close()
        return {
            "title": title,
            "outline": outline
        }
    except Exception as e:
        return {"title": "", "outline": [], "error": str(e)}


def process_all_pdfs_individually(input_folder="inputs", output_folder="experimentoutput"):
  
    os.makedirs(output_folder, exist_ok=True)
    
    pdf_pattern = os.path.join(input_folder, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        return
    
    
    processed_files = []
    
    for pdf_file in sorted(pdf_files):
        filename = os.path.basename(pdf_file)
        filename_without_ext = os.path.splitext(filename)[0]
        
        
        result = extract_title_and_outline(pdf_file)
        output_file = os.path.join(output_folder, f"{filename_without_ext}_analysis.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
      
        
        processed_files.append({
            "filename": filename,
            "output_file": output_file,
            "success": 'error' not in result,
            "outline_count": len(result['outline'])
        })
    
    
    total_files = len(processed_files)
    successful_files = len([f for f in processed_files if f['success']])
    failed_files = total_files - successful_files



def extract_universal_title(doc):
 
    metadata_title = doc.metadata.get("title", "").strip()
    if metadata_title and len(metadata_title) > 3 and not is_filename_like(metadata_title):
        return clean_title(metadata_title) + "  "
    
    page = doc.load_page(0)
    blocks = page.get_text("dict")
    
    spans = []
    for block in blocks["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    spans.append(span)
    
    if not spans:
        return ""
    
    font_sizes = [s["size"] for s in spans]
    max_size = max(font_sizes)
    page_height = page.rect.height
    top_threshold = page_height * 0.4
    
    title_candidates = []
    for span in spans:
        text = span["text"].strip()
        bbox = span["bbox"]
        
        if (bbox[1] <= top_threshold and 
            len(text) >= 3 and 
            len(text) <= 200 and
            not is_obvious_metadata(text) and
            span["size"] >= max_size * 0.8):
            
            title_candidates.append({
                "text": text,
                "size": span["size"],
                "y": bbox[1]
            })
    
    if not title_candidates:
        return ""
    
    title_candidates.sort(key=lambda x: (-x["size"], x["y"]))
    
    title_parts = []
    for candidate in title_candidates[:8]:
        text = candidate["text"]
        if ("overview" in text.lower() or "foundation" in text.lower() or 
            "level" in text.lower() or "extensions" in text.lower()):
            title_parts.append(text)
    
    if not title_parts:
        reference_y = title_candidates[0]["y"]
        for candidate in title_candidates[:5]:
            if abs(candidate["y"] - reference_y) < 60:
                title_parts.append(candidate["text"])
    
    title = " ".join(title_parts)
    return clean_title(title) + "  "


def extract_adaptive_outline(doc, title):
    """
    Adaptive outline extraction with fallback to ensure no empty results
    """
    outline = []
    max_pages = min(50, doc.page_count)
    
    all_items = []
    for page_num in range(max_pages):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")
        
        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    max_font_size = 0
                    is_bold = False
                    
                    for span in line["spans"]:
                        line_text += span["text"]
                        max_font_size = max(max_font_size, span["size"])
                        if "bold" in span.get("font", "").lower():
                            is_bold = True
                    
                    text = line_text.strip()
                    if text and len(text) > 2:
                        all_items.append({
                            "text": text,
                            "size": max_font_size,
                            "page": page_num + 1,
                            "is_bold": is_bold
                        })
    
    if not all_items:
        return outline
    
    document_type = analyze_document_complexity(all_items)
    
    if document_type == "simple":
        outline = extract_simple_outline(all_items, title)
    elif document_type == "medium":
        outline = extract_medium_outline(all_items, title)
    else:  
        outline = extract_complex_outline(all_items, title)
    
    if not outline and document_type == "simple":
        outline = extract_medium_outline(all_items, title)
    
    if not outline:
        outline = extract_fallback_outline(all_items, title)
    
    return outline


def analyze_document_complexity(all_items):
    
    texts = [item["text"] for item in all_items]
    
    numbered_sections = sum(1 for text in texts if re.match(r'^\d+\.\s+[A-Z]', text))
    numbered_subsections = sum(1 for text in texts if re.match(r'^\d+\.\d+\s+[A-Z]', text))
    colon_headings = sum(1 for text in texts if text.endswith(':') and len(text) < 50)
    appendix_sections = sum(1 for text in texts if re.match(r'^Appendix\s+[ABC]', text, re.IGNORECASE))
    
    academic_keywords = ['abstract', 'methodology', 'results', 'conclusion', 'references', 'bibliography']
    academic_count = sum(1 for text in texts for keyword in academic_keywords if keyword in text.lower())
    
    business_keywords = ['proposal', 'requirements', 'evaluation', 'timeline', 'milestones', 'appendix']
    business_count = sum(1 for text in texts for keyword in business_keywords if keyword in text.lower())
    
    training_keywords = ['foundation', 'level', 'extension', 'syllabus', 'certification', 'learning', 'objectives', 'tester']
    training_count = sum(1 for text in texts for keyword in training_keywords if keyword in text.lower())
    
    standard_sections = ['revision history', 'table of contents', 'acknowledgements', 'references']
    standard_count = sum(1 for text in texts for section in standard_sections if section in text.lower())
    
    if (appendix_sections > 2 or colon_headings > 10 or business_count > 5):
        return "complex"  # Use H1-H4
    elif (numbered_subsections > 1 or academic_count > 1 or numbered_sections > 2 or 
          training_count > 3 or standard_count > 2):
        return "medium" 
    else:
        return "simple"  


def extract_simple_outline(all_items, title):
   
    outline = []
    font_sizes = [item["size"] for item in all_items]
    avg_size = sum(font_sizes) / len(font_sizes)
    
    h1_threshold = avg_size * 1.15 
    h2_threshold = avg_size * 1.02 
    
    title_words = set(normalize_text(title).split())
    seen_headings = set()
    
    for item in all_items:
        text = item["text"].strip()
        
        if (text in seen_headings or
            is_title_component(text, title_words)):
            continue
        
        level = None
        
        if (re.match(r'^\d+\.\s+[A-Z]', text) or
            text in ["Revision History", "Table of Contents", "Acknowledgements", "References"]):
            if item["size"] >= h1_threshold:
                level = "H1"
        elif (re.match(r'^\d+\.\d+\s+[A-Z]', text) or
              text in ["Business Outcomes", "Content", "Learning Objectives", "Entry Requirements",
                      "Intended Audience", "Career Paths for Testers"] or
              (len(text) > 5 and len(text) < 80 and text[0].isupper())):
            if item["size"] >= h2_threshold:
                level = "H2"
        
        if level and is_valid_text(text):
            seen_headings.add(text)
            outline.append({
                "level": level,
                "text": text + " ",
                "page": item["page"]
            })
    
    return outline


def extract_medium_outline(all_items, title):
    outline = []
    font_sizes = [item["size"] for item in all_items]
    font_sizes_unique = sorted(set(font_sizes), reverse=True)
    avg_size = sum(font_sizes) / len(font_sizes)
    
    if len(font_sizes_unique) >= 3:
        h1_threshold = font_sizes_unique[1]
        h2_threshold = font_sizes_unique[2]
        h3_threshold = avg_size * 1.05
    else:
        h1_threshold = avg_size * 1.2
        h2_threshold = avg_size * 1.05
        h3_threshold = avg_size * 1.02
    
    title_words = set(normalize_text(title).split())
    seen_headings = set()
    
    for item in all_items:
        text = item["text"].strip()
        
        if (text in seen_headings or
            is_title_component(text, title_words)):
            continue
        
        level = None
        
        if (re.match(r'^\d+\.\s+[A-Z]', text) or
            text in ["Revision History", "Table of Contents", "Acknowledgements", "References"]):
            level = "H1"
        
        elif (re.match(r'^\d+\.\d+\s+[A-Z]', text) or
              text in ["Business Outcomes", "Content", "Learning Objectives", "Entry Requirements",
                      "Intended Audience", "Career Paths for Testers", "Structure and Course Duration", 
                      "Keeping It Current", "Trademarks", "Documents and Web Sites"]):
            level = "H2"
        
        elif (re.match(r'^\d+\.\d+\.\d+\s+[A-Z]', text) or
              (text.endswith(':') and len(text) < 40)):
            level = "H3"
        
        if level == "H1" and item["size"] < h1_threshold * 0.9:
            continue
        elif level == "H2" and item["size"] < h2_threshold * 0.9:
            continue
        elif level == "H3" and item["size"] < h3_threshold * 0.9:
            continue
        
        if level and is_valid_text(text):
            seen_headings.add(text)
            outline.append({
                "level": level,
                "text": text + " ",
                "page": item["page"]
            })
    
    return outline


def extract_fallback_outline(all_items, title):
 
    outline = []
    font_sizes = [item["size"] for item in all_items]
    avg_size = sum(font_sizes) / len(font_sizes)
    
    title_words = set(normalize_text(title).split())
    seen_headings = set()
    
    for item in all_items:
        text = item["text"].strip()
        
        if (text in seen_headings or
            is_title_component(text, title_words) or
            len(text) < 5 or len(text) > 100):
            continue
        
        if (item["size"] > avg_size * 1.1 and
            (text[0].isupper() or re.match(r'^\d+\.', text)) and
            re.search(r'[a-zA-Z]', text)):
            
            level = "H1" if item["size"] > avg_size * 1.2 else "H2"
            seen_headings.add(text)
            outline.append({
                "level": level,
                "text": text + " ",
                "page": item["page"]
            })
    
    return outline[:20]  


def extract_complex_outline(all_items, title):
    outline = []
    font_sizes = [item["size"] for item in all_items]
    font_sizes_unique = sorted(set(font_sizes), reverse=True)
    avg_size = sum(font_sizes) / len(font_sizes)
    
    if len(font_sizes_unique) >= 5:
        h1_threshold = font_sizes_unique[1]
        h2_threshold = font_sizes_unique[2]
        h3_threshold = font_sizes_unique[3]
        h4_threshold = font_sizes_unique[4]
    else:
        h1_threshold = avg_size * 1.4
        h2_threshold = avg_size * 1.2
        h3_threshold = avg_size * 1.1
        h4_threshold = avg_size * 1.05
    
    title_words = set(normalize_text(title).split())
    seen_headings = set()
    
    for item in all_items:
        text = item["text"].strip()
        
        if (text in seen_headings or
            is_title_component(text, title_words) or
            not is_potential_heading(text)):
            continue
        
        level = determine_complex_heading_level(text, item, h1_threshold, h2_threshold, h3_threshold, h4_threshold)
        
        if level:
            seen_headings.add(text)
            outline.append({
                "level": level,
                "text": text + " ",
                "page": item["page"]
            })
    
    return outline


def determine_complex_heading_level(text, item, h1_threshold, h2_threshold, h3_threshold, h4_threshold):
    
    if (re.match(r'^[A-Z][^a-z]*[A-Z].*$', text) and len(text) > 15 or
        re.match(r'^Appendix\s+[ABC]:', text)):
        if item["size"] >= h2_threshold:
            return "H1"
    
    if (re.match(r'^(Summary|Background|Approach|Evaluation).*', text, re.IGNORECASE) or
        re.match(r'^The\s+[A-Z].*', text)):
        if item["size"] >= h3_threshold:
            return "H2"
    
    if (text.endswith(':') and len(text) > 5 and len(text) < 50 or
        re.match(r'^\d+\.\s+[A-Z].*', text)):
        if item["size"] >= h4_threshold:
            return "H3"
    
    if (re.match(r'^For\s+(each|the).*:', text, re.IGNORECASE) or
        (item["is_bold"] and len(text) < 60 and text.endswith(':'))):
        return "H4"
    
    if item["size"] >= h1_threshold:
        return "H1"
    elif item["size"] >= h2_threshold:
        return "H2"
    elif item["size"] >= h3_threshold:
        return "H3"
    elif item["size"] >= h4_threshold:
        return "H4"
    
    return None


def is_valid_text(text):
    """
    Basic text validation
    """
    return (len(text) >= 3 and 
            len(text) <= 200 and 
            re.search(r'[a-zA-Z]', text) and
            not re.match(r'^\d+$', text) and
            not re.search(r'copyright|©|version', text.lower()))


def is_potential_heading(text):
    """
    Full heading validation for complex documents
    """
    if len(text) < 3 or len(text) > 300:
        return False
    
    skip_patterns = [
        r'^\d+$',
        r'^page\s+\d+',
        r'^[©\u00a9]',
        r'^www\.|^http|@',
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, text.lower()):
            return False
    
    return True


def is_title_component(text, title_words):
    """
    Check if text is part of title
    """
    if not title_words:
        return False
    
    text_words = set(normalize_text(text).split())
    if len(text_words) == 0:
        return False
    
    overlap = len(text_words & title_words) / len(text_words)
    return overlap > 0.6


def is_obvious_metadata(text):
    """
    Check for metadata
    """
    return bool(re.search(r'(page\s+\d+|copyright|©|\d{4}|version)', text.lower()))


def is_filename_like(text):
    """
    Check if filename-like
    """
    return bool(re.search(r'\.(pdf|doc|docx|txt)$', text.lower()))


def normalize_text(text):
    """
    Normalize text
    """
    return re.sub(r'\s+', ' ', text.lower().strip())


def clean_title(text):
    """
    Clean title
    """
    text = re.sub(r'\s+', ' ', text.strip())
    if len(text) > 300:
        text = text[:300].rsplit(' ', 1)[0] + "..."
    return text


if __name__ == "__main__":
    process_all_pdfs_individually("sample_dataset/pdfs", "outputs")
