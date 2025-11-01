# Image processing and OCR for license plate recognition
# Handles plate detection, character recognition, and image preprocessing

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from paddleocr import TextRecognition
from typing import List, Tuple, Optional, Dict, Any
import logging
from datetime import datetime
import os
import re

from backend.core.config import settings

logger = logging.getLogger(__name__)

class LicensePlateProcessor:
    """
    Main class for license plate detection and OCR processing.
    Handles the complete pipeline from image input to text recognition.
    """
    
    def __init__(self):
        """Initialize the license plate processor with models and configurations."""
        self.detection_model = None
        self.ocr_reader = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load models
        self._load_models()
        
        # Processing parameters
        self.detection_confidence = settings.PLATE_DETECTION_CONFIDENCE
        self.ocr_confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
    
    def _load_models(self):
        """Load YOLO detection model and OCR reader."""
        try:
            # Load YOLO model for plate detection
            # In production, this should be a custom trained model for Algerian plates
            model_path = os.path.join(settings.MODELS_DIR, "yolo_plate_detection.pt")

            if os.path.exists(model_path):
                self.detection_model = YOLO(model_path).to(self.device)
            else:
                # Use pre-trained YOLOv8 model as fallback
                logger.warning("Custom plate detection model not found")
                raise Exception("yolo_plate_detection")

            self.ocr_reader = TextRecognition(
                model_name="PP-OCRv5_mobile_rec",
                device='gpu' if torch.cuda.is_available() else 'cpu',
            )
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better plate detection and OCR.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            # Simple contrast + brightness normalization
            enhanced = cv2.convertScaleAbs(image, alpha=1.3, beta=10)

            # Light sharpening (cheap)
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            final = cv2.GaussianBlur(sharpened, (3, 3), 0)

            return final

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image


    def detect_license_plates(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect license plates in the image using YOLO.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List[Dict]: List of detected plates with bounding boxes and confidence
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Run YOLO detection
            license_plate_detections = self.detection_model(processed_image, conf=self.detection_confidence)[0]

            # detect license plates
            license_plates = []
            for box in license_plate_detections.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = box.conf[0].cpu().numpy()

                license_plates.append([x1, y1, x2, y2, confidence])

            return np.asarray(license_plates) if license_plates else np.empty((0, 5))
            
        except Exception as e:
            logger.error(f"Error detecting license plates: {e}")
            return []
    
    def extract_plate_roi(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract Region of Interest (ROI) for license plate.
        
        Args:
            image: Input image
            bbox: Bounding box coordinates (x1, y1, x2, y2)
            
        Returns:
            np.ndarray: Cropped plate image
        """
        try:
            x1, y1, x2, y2 = bbox
            
            # Ensure coordinates are within image bounds
            h, w = image.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            # Extract ROI
            roi = image[y1:y2, x1:x2]
            
            # Resize ROI for better OCR (maintain aspect ratio)
            target_height = 64
            aspect_ratio = roi.shape[1] / roi.shape[0]
            target_width = int(target_height * aspect_ratio)
            
            roi_resized = cv2.resize(roi, (target_width, target_height))
            
            return roi_resized
            
        except Exception as e:
            logger.error(f"Error extracting plate ROI: {e}")
            return image
    
    def enhance_plate_image(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Enhance plate image for better OCR results.
        
        Args:
            plate_image: Cropped plate image
            
        Returns:
            np.ndarray: Enhanced plate image
        """
        try:
            # Convert to grayscale if needed
            if len(plate_image.shape) == 3:
                gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_image.copy()

            gray = cv2.bilateralFilter(gray, 11, 17, 17)

            # Deskew the image
            edges = cv2.Canny(gray, 100, 200)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40,
                                    minLineLength=30, maxLineGap=100)

            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle_rad = np.arctan2(y2 - y1, x2 - x1)
                    angle_deg = np.degrees(angle_rad)
                    if -80 < angle_deg < 80:
                        angles.append(angle_deg)

                (h, w) = plate_image.shape[:2]
                center = (w // 2, h // 2)
                # angle = float(angles[0])
                angle = float(np.mean(angles))

                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                plate_image = cv2.warpAffine(plate_image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

            # Morphological operations to clean up the image
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(plate_image, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            logger.error(f"Error enhancing plate image: {e}")
            return plate_image

    def _validate_plate_text(self, text: str) -> bool:
        pattern = re.compile(r'^\d{10,11}$')
        return bool(pattern.match(text))
    
    def recognize_plate_text(self, plate_image: np.ndarray, track_id: int) -> Dict[str, Any]:
        """
        Recognize text from license plate image using OCR.
        
        Args:
            plate_image: Enhanced plate image
            
        Returns:
            Dict: OCR results with text and confidence
        """
        try:
            # Enhance the plate image
            enhanced_image = self.enhance_plate_image(plate_image)
            
            paddleocr_results = self.ocr_reader.predict(enhanced_image, batch_size=1)

            if len(paddleocr_results) > 0:
                text = paddleocr_results[0].get('rec_text') or ""
                confidence = paddleocr_results[0].get('rec_score') or 0

                cleaned_text = self._clean_plate_text(text)

                if confidence >= self.ocr_confidence_threshold and self._validate_plate_text(cleaned_text):
                    return {
                        'text': cleaned_text,
                        'confidence': confidence,
                        'method': 'paddleocr',
                        'raw_text': text
                    }

            return {
                'text': '',
                'confidence': 0.0,
                'method': 'none',
                'raw_text': ''
            }
            
        except Exception as e:
            logger.error(f"Error recognizing plate text: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'error',
                'raw_text': '',
                'error': str(e)
            }
    
    def _clean_plate_text(self, text: str) -> str:
        """
        Clean and normalize license plate text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            str: Cleaned and normalized text
        """
        try:
            # Remove extra whitespace and convert to uppercase
            cleaned = text.strip().upper()
            
            # Common character corrections for Algerian plates
            corrections = {
                'O': '0',  # Letter O to number 0
                'I': '1',  # Letter I to number 1
                'S': '5',  # Letter S to number 5
                'B': '8',  # Letter B to number 8
                'G': '6',
                '|': '1',
                ']': '1',
                'J': '3',
                'A': '4'
            }
            
            # Apply corrections
            for old, new in corrections.items():
                cleaned = cleaned.replace(old, new)

            cleaned = ''.join(c for c in cleaned if c.isalnum())
            # cleaned = ' '.join(cleaned.split())
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning plate text: {e}")
            return text
    
    def save_plate_thumbnail(self, plate_image: np.ndarray, detection_id: str) -> str:
        """
        Save plate thumbnail for audit purposes.
        
        Args:
            plate_image: Plate image to save
            detection_id: Unique detection identifier
            
        Returns:
            str: Path to saved thumbnail
        """
        try:
            # Create thumbnails directory
            thumbnails_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
            os.makedirs(thumbnails_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plate_{detection_id}_{timestamp}.jpg"
            filepath = os.path.join(thumbnails_dir, filename)
            
            # Save image
            cv2.imwrite(filepath, plate_image)
            
            logger.info(f"Saved plate thumbnail: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving plate thumbnail: {e}")
            return ""

    def annotate_frame(self, frame: np.ndarray, results) -> np.ndarray:
        annotated_frame = frame.copy()

        for res in results:
            detection = res['detection']
            overall_confidence = float(res['overall_confidence'])

            # TODO make color dynamic
            color = (0, 255, 0)

            x1, y1, x2, y2 = detection['bbox']
            width, height = x2 - x1, y2 - y1
            id = detection['id']

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{id}: {res['ocr']['text']} ({overall_confidence:.2f})"
            cv2.putText( annotated_frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

        return annotated_frame
