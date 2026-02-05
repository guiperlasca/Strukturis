from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QPainter, QWheelEvent
import cv2

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.transformationAnchor = QGraphicsView.AnchorUnderMouse
        self.resizeAnchor = QGraphicsView.AnchorUnderMouse
        
        self.item = None
        self._zoom = 0
        
        # Crop State
        self.drawing_crop = False
        self.crop_start = None
        self.crop_rect_item = None

    def set_image(self, cv_image):
        if cv_image is None: return
        self.scene.clear()
        self.crop_rect_item = None
        self.image_item = None

        # Handle Grayscale vs Color
        if len(cv_image.shape) == 2:
            height, width = cv_image.shape
            bytes_per_line = width
            q_img = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        else:
            height, width, channel = cv_image.shape
            bytes_per_line = 3 * width
            q_img = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        pixmap = QPixmap.fromImage(q_img)
        
        self.item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.item)
        self.fitInView(self.item, Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(1.25, 1.25)
        else:
            self.scale(0.8, 0.8)

    def toggle_crop_mode(self, enabled):
        """Switches between Pan (ScrollHand) and Crop (NoDrag)."""
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ArrowCursor)
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = None

    def mousePressEvent(self, event):
        if self.dragMode() == QGraphicsView.NoDrag and event.button() == Qt.LeftButton:
            self.drawing_crop = True
            pos = self.mapToScene(event.position().toPoint())
            self.crop_start = pos
            
            from PySide6.QtWidgets import QGraphicsRectItem
            from PySide6.QtGui import QPen, QColor
            if not self.crop_rect_item:
                self.crop_rect_item = QGraphicsRectItem()
                self.crop_rect_item.setPen(QPen(QColor(255, 0, 0), 2))
                self.scene.addItem(self.crop_rect_item)
            self.crop_rect_item.setRect(pos.x(), pos.y(), 0, 0)
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing_crop and self.crop_rect_item:
            pos = self.mapToScene(event.position().toPoint())
            x = min(self.crop_start.x(), pos.x())
            y = min(self.crop_start.y(), pos.y())
            w = abs(self.crop_start.x() - pos.x())
            h = abs(self.crop_start.y() - pos.y())
            self.crop_rect_item.setRect(x, y, w, h)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing_crop and event.button() == Qt.LeftButton:
            self.drawing_crop = False
            # Keep the rect visible so user can see what they selected before confirming
        super().mouseReleaseEvent(event)

    def get_crop_rect_coords(self):
        """Returns (x, y, w, h) relative to the original image pixels."""
        if not self.crop_rect_item or not self.item:
            return None
            
        r = self.crop_rect_item.rect()
        
        # Check integrity
        if r.width() < 5 or r.height() < 5: return None
        
        # Map scene coords to item coords is usually 1:1 if item is at 0,0 and not scaled independent of scene
        # But image item might be transformed? Usually QGraphicsPixmapItem is just added.
        # Let's map rect to item local coords just in case.
        
        # Simple assumption: Item is at 0,0.
        # Need to clamp to image bounds
        
        img_w = self.item.pixmap().width()
        img_h = self.item.pixmap().height()
        
        x = max(0, int(r.x()))
        y = max(0, int(r.y()))
        w = min(int(r.width()), img_w - x)
        h = min(int(r.height()), img_h - y)
        
        return (x, y, w, h)
