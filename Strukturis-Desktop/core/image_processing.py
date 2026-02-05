import cv2
import numpy as np
import fitz # PyMuPDF

class ImageProcessing:
    @staticmethod
    def load_image(path):
        """Loads image handling unicode paths correctly."""
        # Visual loading via numpy to handle non-ascii paths on Windows
        stream = open(path, "rb")
        bytes = bytearray(stream.read())
        numpyarray = np.asarray(bytes, dtype=np.uint8)
        img = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)
        return img

    @staticmethod
    def load_pdf_as_image(path, page_index=0):
        """Renders a PDF page as an OpenCV image."""
        try:
            doc = fitz.open(path)
            if page_index >= len(doc):
                return None
            
            page = doc.load_page(page_index)
            # Render at 300 DPI (approx zoom=4 for 72dpi base)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
            
            # Convert to numpy
            if pix.n < 3:
                # Grayscale
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                # RGB / RGBA
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                elif pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                    
            return img
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return None

    @staticmethod
    def get_pdf_page_count(path):
        try:
            doc = fitz.open(path)
            return len(doc)
        except:
            return 0

    @staticmethod
    def to_grayscale(img):
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    def deskew_image(img):
        """
        Detects text orientation and auto-rotates.
        """
        gray = ImageProcessing.to_grayscale(img)
        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Rotate logic
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated, angle

    @staticmethod
    def rotate_image(img, angle=90):
        """Rotates image by arbitrary angle."""
        # Standard rotations for speed/quality
        if angle == 90:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        elif angle == 270 or angle == -90:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif angle == 0:
            return img
            
        # Arbitrary rotation
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, -angle, 1.0) # Negative for intuitive direction
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    @staticmethod
    def apply_bw_filter(img):
        """Applies binary thresholding (Black & White)."""
        gray = ImageProcessing.to_grayscale(img)
        # Otsu's binarization
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    @staticmethod
    def adjust_contrast(img, alpha=1.5, beta=0):
        """
        Alpha: Contrast control (1.0-3.0)
        Beta: Brightness control (0-100)
        """
        return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
