#!/usr/bin/env python3
"""
Remove NotebookLM watermark from full-page images in PDF.
Since the PDF is made of full-page PNG images with the watermark baked in,
we need to edit the images directly.
"""

import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import os

def remove_watermark_from_image(img_bytes, watermark_region, fill_color=None):
    """
    Remove watermark by covering with background color or inpainting.
    
    watermark_region: (x1, y1, x2, y2) tuple defining the watermark area
    fill_color: RGB tuple to fill, or None to sample from nearby area
    """
    img = Image.open(io.BytesIO(img_bytes))
    
    x1, y1, x2, y2 = watermark_region
    
    if fill_color is None:
        # Sample color from just above/beside the watermark region
        sample_x = x1 + 10
        sample_y = max(0, y1 - 10)
        fill_color = img.getpixel((sample_x, sample_y))
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    draw.rectangle([x1, y1, x2, y2], fill=fill_color)
    
    # Convert back to bytes
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

def remove_watermark_smart(img_bytes, position="bottom-right"):
    """
    Smart watermark removal that samples the background color.
    NotebookLM typically places watermark in bottom-right or bottom-left.
    """
    img = Image.open(io.BytesIO(img_bytes))
    width, height = img.size
    
    # Define watermark regions based on position
    # NotebookLM watermark is typically about 150-200px wide, 20-30px tall
    regions = {
        "bottom-right": (width - 220, height - 35, width - 5, height - 5),
        "bottom-left": (5, height - 35, 220, height - 5),
        "bottom-center": (width//2 - 110, height - 35, width//2 + 110, height - 5),
        "top-right": (width - 220, 5, width - 5, 35),
        "top-left": (5, 5, 220, 35),
    }
    
    region = regions.get(position, regions["bottom-right"])
    x1, y1, x2, y2 = region
    
    # Sample background color from multiple points around the region
    sample_points = [
        (x1 - 5, y1 + (y2-y1)//2),  # Left of region
        (x1, y1 - 5),  # Above region
        (x2, y1 - 5),  # Above right
    ]
    
    colors = []
    for px, py in sample_points:
        if 0 <= px < width and 0 <= py < height:
            colors.append(img.getpixel((px, py)))
    
    if colors:
        # Average the sampled colors
        if len(colors[0]) == 4:  # RGBA
            avg_color = tuple(sum(c[i] for c in colors) // len(colors) for i in range(4))
        else:  # RGB
            avg_color = tuple(sum(c[i] for c in colors) // len(colors) for i in range(3))
    else:
        avg_color = (0, 0, 0)  # Default to black
    
    # Draw rectangle over watermark
    draw = ImageDraw.Draw(img)
    draw.rectangle([x1, y1, x2, y2], fill=avg_color)
    
    # Convert back to bytes
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

def process_pdf(input_path, output_path, watermark_position="bottom-right"):
    """Process PDF and remove watermark from each page image."""
    doc = fitz.open(input_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            
            # Remove watermark from this image
            cleaned_bytes = remove_watermark_smart(img_bytes, watermark_position)
            
            # Replace the image in the PDF
            doc.xref_set_key(xref, "Subtype", "/Image")
            
            # Create new image
            new_img = fitz.Pixmap(cleaned_bytes)
            
            # Get the image rectangle on the page
            rects = page.get_image_rects(img)
            if rects:
                rect = rects[0]
                # Remove old image and insert new one
                page.add_redact_annot(rect)
                page.apply_redactions()
                page.insert_image(rect, pixmap=new_img)
            
            print(f"Processed page {page_num + 1}")
    
    doc.save(output_path)
    doc.close()
    print(f"\nSaved to: {output_path}")

def process_images_then_rebuild_pdf(input_path, output_path, watermark_positions=None):
    """
    Alternative approach: extract images, clean them, rebuild PDF.
    """
    if watermark_positions is None:
        # Try multiple common positions
        watermark_positions = ["bottom-right", "bottom-left", "bottom-center"]
    
    doc = fitz.open(input_path)
    new_doc = fitz.open()  # Create new PDF
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        if not images:
            # No images, copy page as-is
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            continue
        
        # Get the first (full-page) image
        img = images[0]
        xref = img[0]
        base_image = doc.extract_image(xref)
        img_bytes = base_image["image"]
        
        # Clean watermark from all specified positions
        cleaned_bytes = img_bytes
        for pos in watermark_positions:
            cleaned_bytes = remove_watermark_smart(cleaned_bytes, pos)
        
        # Create new page with same dimensions
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        
        # Insert cleaned image
        pix = fitz.Pixmap(cleaned_bytes)
        new_page.insert_image(new_page.rect, pixmap=pix)
        
        print(f"Processed page {page_num + 1}")
    
    new_doc.save(output_path)
    new_doc.close()
    doc.close()
    print(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    input_pdf = "/home/seyominaoto/Videos/AgentAuth/AgentAuth_pitch_deck.pdf"
    output_pdf = "/home/seyominaoto/Videos/AgentAuth/AgentAuth_pitch_deck_clean.pdf"
    
    # Most common position for NotebookLM watermark
    print("Removing watermark from bottom-right, bottom-left, and bottom-center...")
    process_images_then_rebuild_pdf(
        input_pdf, 
        output_pdf, 
        watermark_positions=["bottom-right", "bottom-left", "bottom-center"]
    )
    
    print("\nDone! Check the output file.")
    print("If watermark is still visible, please tell me the exact position (corner/location)")
    print("and I can adjust the removal area.")
