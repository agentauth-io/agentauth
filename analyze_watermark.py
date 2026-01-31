#!/usr/bin/env python3
"""
Deeper analysis to find and remove NotebookLM watermark (likely an image).
"""

import fitz  # PyMuPDF
import os
from PIL import Image
import io

def extract_and_analyze_images(input_path, output_dir):
    """Extract all images from PDF for analysis."""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(input_path)
    
    print(f"Analyzing {len(doc)} pages for images...")
    
    all_images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            width = base_image["width"]
            height = base_image["height"]
            
            # Save image for inspection
            img_filename = f"page{page_num+1}_img{img_index+1}_{width}x{height}.{image_ext}"
            img_path = os.path.join(output_dir, img_filename)
            
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"Page {page_num+1}: Image {img_index+1} - {width}x{height} - {img_filename}")
            
            all_images.append({
                "page": page_num,
                "xref": xref,
                "width": width,
                "height": height,
                "filename": img_filename
            })
    
    doc.close()
    return all_images

def find_watermark_images(images, page_width=1376, page_height=768):
    """
    Identify potential watermark images.
    NotebookLM watermarks are typically:
    - Small relative to page size
    - Present on every page
    - Or in a specific corner
    """
    
    # Group by dimensions to find repeating images
    dimension_groups = {}
    for img in images:
        key = (img["width"], img["height"])
        if key not in dimension_groups:
            dimension_groups[key] = []
        dimension_groups[key].append(img)
    
    print("\n=== Image dimension analysis ===")
    for dims, imgs in sorted(dimension_groups.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(imgs)
        percentage = (dims[0] * dims[1]) / (page_width * page_height) * 100
        print(f"  {dims[0]}x{dims[1]}: appears {count} times, covers {percentage:.1f}% of page")
        
        # Watermarks often appear on many/all pages and are small
        if count >= 5 and percentage < 5:
            print(f"    ^ LIKELY WATERMARK (small, appears on {count} pages)")

def remove_small_repeated_images(input_path, output_path, max_size_percent=3, min_occurrences=3):
    """
    Remove images that appear on multiple pages and are small (likely watermarks).
    """
    doc = fitz.open(input_path)
    page_area = doc[0].rect.width * doc[0].rect.height
    
    # Collect all image xrefs with their sizes
    image_info = {}
    for page_num in range(len(doc)):
        page = doc[page_num]
        for img in page.get_images(full=True):
            xref = img[0]
            if xref not in image_info:
                base_image = doc.extract_image(xref)
                image_info[xref] = {
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "pages": [],
                    "size_percent": (base_image["width"] * base_image["height"]) / page_area * 100
                }
            image_info[xref]["pages"].append(page_num)
    
    # Find watermark candidates
    watermark_xrefs = []
    for xref, info in image_info.items():
        if info["size_percent"] < max_size_percent and len(info["pages"]) >= min_occurrences:
            print(f"Potential watermark: xref={xref}, {info['width']}x{info['height']}, "
                  f"on {len(info['pages'])} pages, {info['size_percent']:.2f}% of page")
            watermark_xrefs.append(xref)
    
    if not watermark_xrefs:
        print("No small repeated images found. Trying different approach...")
        # Look for any small image that appears on most pages
        for xref, info in image_info.items():
            if len(info["pages"]) >= len(doc) - 2:  # On almost all pages
                print(f"Found image on most pages: xref={xref}, {info['width']}x{info['height']}")
                watermark_xrefs.append(xref)
    
    doc.close()
    
    if watermark_xrefs:
        print(f"\nRemoving {len(watermark_xrefs)} potential watermark images...")
        remove_images_by_xref(input_path, output_path, watermark_xrefs)
    else:
        print("\nNo watermark images identified automatically.")
        print("The watermark might be part of the page content stream (vector graphics).")

def remove_images_by_xref(input_path, output_path, xrefs_to_remove):
    """Remove specific images by their xref numbers."""
    doc = fitz.open(input_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        for img in images:
            xref = img[0]
            if xref in xrefs_to_remove:
                # Get image rectangle and redact it
                img_rects = page.get_image_rects(img)
                for rect in img_rects:
                    # Add white rectangle over the image position
                    page.add_redact_annot(rect, fill=(1, 1, 1))
        
        page.apply_redactions()
    
    doc.save(output_path)
    doc.close()
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    input_pdf = "/home/seyominaoto/Videos/AgentAuth/AgentAuth_pitch_deck.pdf"
    output_dir = "/home/seyominaoto/Videos/AgentAuth/pdf_images"
    output_pdf = "/home/seyominaoto/Videos/AgentAuth/AgentAuth_pitch_deck_nowatermark.pdf"
    
    print("=== Extracting images ===")
    images = extract_and_analyze_images(input_pdf, output_dir)
    
    print("\n=== Analyzing for watermarks ===")
    find_watermark_images(images)
    
    print("\n=== Attempting automatic removal ===")
    remove_small_repeated_images(input_pdf, output_pdf)
