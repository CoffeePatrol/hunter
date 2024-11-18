import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from pathlib import Path

def download_images(url, output_dir='downloaded_images'):
    """
    Download all images from a webpage, particularly focusing on webp images in hyperlinks.
    
    Args:
        url (str): The webpage URL to scrape
        output_dir (str): Directory to save the downloaded images
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Fetch the webpage
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all images, both direct and within links
    images = []
    
    # Direct img tags
    images.extend(soup.find_all('img'))
    
    # Images within links
    for link in soup.find_all('a'):
        images.extend(link.find_all('img'))
    
    # Download each image
    for i, img in enumerate(images, 1):
        # Get image URL
        img_url = img.get('src')
        if not img_url:
            continue
            
        # Convert relative URLs to absolute URLs
        img_url = urljoin(url, img_url)
        
        try:
            # Fetch image
            img_response = requests.get(img_url)
            img_response.raise_for_status()
            
            # Generate filename
            parsed_url = urlparse(img_url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f'image_{i}.webp'
            elif not os.path.splitext(filename)[1]:
                filename += '.webp'
                
            # Save image
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            print(f"Downloaded: {filename}")
            
        except requests.RequestException as e:
            print(f"Error downloading {img_url}: {e}")
            continue

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    download_images(url)