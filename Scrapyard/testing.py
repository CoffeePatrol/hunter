# Setup and usage example
from icon_extractor import IconExtractor

# Initialize the extractor
extractor = IconExtractor()

# Extract icons from creature tables
extractor.extract_icons("creature1.png")
extractor.extract_icons("creature2.png")

# Extract region icons
extractor.extract_region_icons("region.png")