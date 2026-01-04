"""
configuration file for Traction project.
"""

import platform
from pathlib import Path
import os


# Data directory paths based on operating system
if platform.system() == 'Windows':
    data_dir = Path(r"C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\Faltermeier, Julia's files - FIP Traction of IMF surveillance\temp\data")
    raw_xml_dir = Path(r"C:\Users\chuang\OneDrive - International Monetary Fund (PRD)\AI tools\Data\ArticleIV_xml_updated")
else:  # Linux/Ubuntu
    data_dir = Path('/data/home/xiong/data/Fund/CSR/Tractions')
    raw_xml_dir = os.path.join(data_dir, 'ArticleIV_xml_updated')
    
