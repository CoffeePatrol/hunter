import cv2
import numpy as np
from PIL import Image
import os
import pytesseract
from typing import Tuple, List, Dict
import re

class IconExtractor:
    def __init__(self):
        # Define expected icon sizes and positions
        self.creature_icon_size = (24, 24)  # Approximate size for creature icons
        self.method_icon_size = (20, 20)    # Approximate size for method icons
        self.region_icon_size = (30, 20)    # Approximate size for region shields
        
        # Column positions (approximate x-coordinates)
        self.creature_col_x = 50  # X coordinate where creature icons typically appear
        self.method_col_x = 400   # X coordinate where method icons typically appear
        
        # OCR configuration
        self.tesseract_config = '--psm 6'  # Assume uniform text block
        self.min_confidence = 60  # Minimum confidence score for OCR results
        
        # Create output directories
        self.base_dir = "extracted_icons"
        self.dirs = {
            "creatures": os.path.join(self.base_dir, "creatures"),
            "methods": os.path.join(self.base_dir, "methods"),
            "regions": os.path.join(self.base_dir, "regions")
        }
        self._create_directories()
        
        # Initialize mappings for consistent naming and text correction
        self.known_creatures = {
            "kebbit": ["kebbit", "kebit", "keblt"],
            "salamander": ["salamander", "salamender"],
            "chinchompa": ["chinchompa", "chinchornpa"],
            "moth": ["moth", "rnoth"],
            "antelope": ["antelope", "antelose"],
        }
        
        self.known_methods = {
            "spiked_pit": ["spiked pit", "spiked-pit", "spike pit"],
            "box_trap": ["box trap", "boxstrap", "box-trap"],
            "deadfall": ["deadfall", "dead fall", "dead-fall"],
            "falconry": ["falconry", "falconary"],
            "net_trap": ["net trap", "nettrap", "net-trap"],
            "butterfly_net": ["butterfly net", "butterflynet"],
            "tracking": ["tracking", "traking"],
            "bird_snare": ["bird snare", "birdsnare", "bird-snare"]
        }

    def extract_icons(self, image_path: str):
        """Main method to extract icons from the game interface."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rows = self._extract_table_rows(img_rgb)
        
        for row in rows:
            # Extract text from the entire row first
            row_text = self._extract_text_from_row(row)
            
            # Extract and save creature icon
            creature_icon = self._extract_creature_icon(row)
            creature_name = self._get_creature_name(row_text)
            if creature_icon is not None and creature_name:
                self._save_icon(creature_icon, "creatures", creature_name)
            
            # Extract and save method icon
            method_icon = self._extract_method_icon(row)
            method_name = self._get_method_name(row_text)
            if method_icon is not None and method_name:
                self._save_icon(method_icon, "methods", method_name)

    def extract_region_icons(self, image_path: str):
        """Extract region shield icons from the regions interface."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Extract text blocks first
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        text_blocks = self._extract_text_blocks(gray)
        
        # Detect shield-shaped regions
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if self._is_shield_shaped(w, h):
                region_icon = img_rgb[y:y+h, x:x+w]
                region_name = self._get_nearest_text(text_blocks, (x + w//2, y + h//2))
                if region_name:
                    self._save_icon(region_icon, "regions", region_name)

    def _create_directories(self):
        """Create necessary directories for icon storage."""
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)

    def _extract_table_rows(self, img_rgb: np.ndarray) -> List[np.ndarray]:
        """Extract individual rows from the table."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Create horizontal kernel for detecting row separators
        kernel_len = np.array(img_rgb).shape[1]//100
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        
        # Detect horizontal lines (row separators)
        horizontal_lines = cv2.erode(binary, horizontal_kernel, iterations=3)
        horizontal_lines = cv2.dilate(horizontal_lines, horizontal_kernel, iterations=3)
        
        # Find contours of horizontal lines
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get y-coordinates of row boundaries
        row_boundaries = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            row_boundaries.append(y)
        
        # Sort boundaries and add image boundaries
        row_boundaries = [0] + sorted(row_boundaries) + [img_rgb.shape[0]]
        
        # Extract rows
        rows = []
        min_row_height = 20  # Minimum height for a valid row
        
        for i in range(len(row_boundaries) - 1):
            y1 = row_boundaries[i]
            y2 = row_boundaries[i + 1]
            
            # Skip if row is too small
            if y2 - y1 < min_row_height:
                continue
                
            # Extract row
            row = img_rgb[y1:y2, :]
            
            # Skip empty rows
            if not self._is_empty_row(row):
                rows.append(row)
        
        return rows
    
    def _is_empty_row(self, row: np.ndarray) -> bool:
        """Check if a row is empty (contains no meaningful content)."""
        # Convert to grayscale if it's RGB
        if len(row.shape) == 3:
            gray = cv2.cvtColor(row, cv2.COLOR_RGB2GRAY)
        else:
            gray = row
        
        # Calculate the standard deviation of pixel values
        std_dev = np.std(gray)
        
        # If std dev is very low, it's likely an empty row
        return std_dev < 5  # Adjust threshold as needed

    def _extract_creature_icon(self, row: np.ndarray) -> np.ndarray:
        """Extract creature icon from a table row."""
        row_height = row.shape[0]
        # Calculate the vertical center of the row
        center_y = row_height // 2
        
        # Extract region around expected creature icon position
        start_y = max(0, center_y - self.creature_icon_size[1] // 2)
        end_y = min(row_height, center_y + self.creature_icon_size[1] // 2)
        
        # Look for icon in the first column area
        start_x = max(0, self.creature_col_x - self.creature_icon_size[0] // 2)
        end_x = start_x + self.creature_icon_size[0]
        
        if end_x <= row.shape[1] and end_y <= row.shape[0]:  # Ensure within bounds
            icon = row[start_y:end_y, start_x:end_x]
            # Check if the extracted region likely contains an icon (not empty space)
            if self._is_valid_icon(icon):
                return icon
        return None

    def _extract_method_icon(self, row: np.ndarray) -> np.ndarray:
        """Extract method icon from a table row."""
        row_height = row.shape[0]
        # Calculate the vertical center of the row
        center_y = row_height // 2
        
        # Extract region around expected method icon position
        start_y = max(0, center_y - self.method_icon_size[1] // 2)
        end_y = min(row_height, center_y + self.method_icon_size[1] // 2)
        
        # Look for icon in the last column area
        start_x = max(0, self.method_col_x - self.method_icon_size[0] // 2)
        end_x = start_x + self.method_icon_size[0]
        
        if end_x <= row.shape[1] and end_y <= row.shape[0]:  # Ensure within bounds
            icon = row[start_y:end_y, start_x:end_x]
            # Check if the extracted region likely contains an icon (not empty space)
            if self._is_valid_icon(icon):
                return icon
        return None

    def _is_valid_icon(self, icon: np.ndarray) -> bool:
        """Check if extracted region likely contains an icon."""
        if icon is None or icon.size == 0:
            return False
            
        # Convert to grayscale if needed
        if len(icon.shape) == 3:
            gray = cv2.cvtColor(icon, cv2.COLOR_RGB2GRAY)
        else:
            gray = icon
            
        # Calculate the standard deviation of pixel values
        std_dev = np.std(gray)
        
        # If std dev is very low, it's likely empty space
        if std_dev < 10:  # Adjust threshold as needed
            return False
            
        # Check if there's enough non-white pixels
        non_white = np.count_nonzero(gray < 240)  # Adjust threshold as needed
        total_pixels = gray.size
        if non_white / total_pixels < 0.1:  # At least 10% non-white pixels
            return False
            
        return True

    def _extract_text_from_row(self, row: np.ndarray) -> str:
        """Extract all text from a table row using OCR."""
        # Convert to grayscale
        gray = cv2.cvtColor(row, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding to clean up text
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Add padding around text for better OCR
        padded = cv2.copyMakeBorder(thresh, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(padded, config=self.tesseract_config)
        return text.strip().lower()
    
    def _get_creature_name(self, row_text: str) -> str:
        """Extract and normalize creature name from row text."""
        for normalized_name, variants in self.known_creatures.items():
            for variant in variants:
                if variant in row_text:
                    # Extract the full creature name using surrounding context
                    pattern = fr'\b\w+\s*{variant}\b'
                    match = re.search(pattern, row_text)
                    if match:
                        return match.group(0).replace(' ', '_')
        return None    
    
    def _get_method_name(self, row_text: str) -> str:
        """Extract and normalize method name from row text."""
        for normalized_name, variants in self.known_methods.items():
            for variant in variants:
                if variant in row_text:
                    return normalized_name
        return None    
    
    def _extract_text_blocks(self, gray_img: np.ndarray) -> List[Dict]:
        """Extract text blocks with their positions."""
        # Get image data including bounding boxes
        data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)
        
        text_blocks = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) >= self.min_confidence:
                text_blocks.append({
                    'text': data['text'][i].lower(),
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'w': data['width'][i],
                    'h': data['height'][i]
                })
        return text_blocks

    def _get_nearest_text(self, text_blocks: List[Dict], point: Tuple[int, int]) -> str:
        """Find the nearest text block to a given point."""
        min_dist = float('inf')
        nearest_text = None
        
        for block in text_blocks:
            # Calculate distance to center of text block
            block_center = (block['x'] + block['w']//2, block['y'] + block['h']//2)
            dist = np.sqrt((point[0] - block_center[0])**2 + (point[1] - block_center[1])**2)
            
            if dist < min_dist:
                min_dist = dist
                nearest_text = block['text']
        
        return self._clean_filename(nearest_text) if nearest_text else None

    def _is_shield_shaped(self, width: int, height: int) -> bool:
        """Check if the detected contour matches shield icon dimensions."""
        return (
            abs(width - self.region_icon_size[0]) < 5 and
            abs(height - self.region_icon_size[1]) < 5
        )

    def _clean_filename(self, name: str) -> str:
        """Convert name to filesystem-safe filename."""
        if not name:
            return None
        # Remove special characters and convert spaces to underscores
        clean_name = re.sub(r'[^\w\s-]', '', name.lower())
        return clean_name.strip().replace(' ', '_')

    def debug_row_extraction(self, image_path: str):
        """Visualize row extraction for debugging purposes."""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rows = self._extract_table_rows(img_rgb)
        
        # Create debug image with row boundaries
        debug_img = img_rgb.copy()
        current_y = 0
        
        for row in rows:
            # Draw red line at row boundary
            cv2.line(debug_img, (0, current_y), (debug_img.shape[1], current_y), (255, 0, 0), 1)
            current_y += row.shape[0]
        
        # Save debug image
        debug_path = os.path.join(self.base_dir, 'debug_rows.png')
        cv2.imwrite(debug_path, cv2.cvtColor(debug_img, cv2.COLOR_RGB2BGR))
        print(f"Saved debug image to: {debug_path}")
        print(f"Found {len(rows)} rows") 

    def _save_icon(self, icon: np.ndarray, category: str, name: str):
        """Save extracted icon to appropriate directory with cleaned filename.
        
        Args:
            icon: numpy array containing the icon image
            category: category folder ('creatures', 'methods', or 'regions')
            name: name to use for the file
        """
        if name is None:
            return
            
        filename = self._clean_filename(name)
        if filename is None:
            return
            
        output_path = os.path.join(self.dirs[category], f"{filename}.png")
        
        # Convert from numpy array to PIL Image
        icon_pil = Image.fromarray(icon)
        
        # Ensure consistent size based on category
        if category == "creatures":
            size = self.creature_icon_size
        elif category == "methods":
            size = self.method_icon_size
        elif category == "regions":
            size = self.region_icon_size
        
        # Resize if necessary
        if icon_pil.size != size:
            icon_pil = icon_pil.resize(size, Image.Resampling.LANCZOS)
        
        # Save the image
        icon_pil.save(output_path)   

# Example usage
if __name__ == "__main__":
    extractor = IconExtractor()
    
    # Extract from hunting table
    extractor.extract_icons("creature1.png")
    extractor.extract_icons("creature2.png")
    
    # Extract region shields
    extractor.extract_region_icons("regions.png")