"""Enterprise VAPT Word report style constants."""

from docx.shared import Inches, Pt, RGBColor

# Typography
FONT_NAME = "Calibri"
FONT_SIZE = Pt(11)
FONT_SIZE_HEADING = Pt(11)

# Page layout
PAGE_MARGIN = Inches(1.0)

# Brand colors (RGB)
RGB_NAVY_HEADER = RGBColor(31, 56, 100)       # #1F3864 — table headers
RGB_METADATA_LABEL = RGBColor(68, 44, 106)    # #442C6A — metadata label column
RGB_WHITE = RGBColor(255, 255, 255)
RGB_BLACK = RGBColor(0, 0, 0)
RGB_BORDER = RGBColor(89, 89, 89)

# Cell fill (hex without #) for w:shd
FILL_METADATA_LABEL = "442C6A"
FILL_NAVY_HEADER = "1F3864"
FILL_WHITE = "FFFFFF"
FILL_CRITICAL = "C00000"
FILL_HIGH = "ED7D31"
FILL_MEDIUM = "FFC000"
FILL_LOW = "92D050"
FILL_INFORMATIONAL = "B4C6E7"

# Default section numbering prefix (e.g. 5.1, 5.2)
DEFAULT_SECTION_PREFIX = "5"
FINDING_ID_PREFIX = "VAPT"
