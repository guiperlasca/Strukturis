import os
import mimetypes

class FileHandler:
    VALID_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'}
    VALID_PDF_EXT = {'.pdf'}

    @staticmethod
    def identify_file_type(file_path):
        """
        Returns 'image', 'pdf', or None based on extension/mime.
        """
        if not os.path.exists(file_path):
            return None
        
        _, ext = os.path.splitext(file_path.lower())
        
        if ext in FileHandler.VALID_PDF_EXT:
            return 'pdf'
        elif ext in FileHandler.VALID_IMAGE_EXT:
            return 'image'
        
        return None
