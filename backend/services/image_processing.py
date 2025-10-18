# Image processing and OCR pipeline for license plate recognition
# Handles plate detection, character recognition, and image preprocessing

import cv2
import numpy as np
import torch
from ultralytics import YOLO
import easyocr
import pytesseract
from typing import List, Tuple, Optional, Dict, Any
import logging
from datetime import datetime
import os
import json
from backend.services.sort.sort import *
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
        self.tracker = None
        self.ocr_reader = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load models
        self._load_models()
        
        # Processing parameters
        self.detection_confidence = settings.PLATE_DETECTION_CONFIDENCE
        self.ocr_confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
        
        logger.info(f"LicensePlateProcessor initialized on device: {self.device}")
    
    def _load_models(self):
        """Load YOLO detection model and OCR reader."""
        try:
            # Load YOLO model for plate detection
            # In production, this should be a custom trained model for Algerian plates
            model_path = os.path.join(settings.MODELS_DIR, "yolo_plate_detection.pt")

            if os.path.exists(model_path):
                self.detection_model = YOLO(model_path)
            else:
                # Use pre-trained YOLOv8 model as fallback
                logger.warning("Custom plate detection model not found")
                raise Exception("yolo_plate_detection")

            self.tracker = Sort()
            
            # Initialize EasyOCR reader for Arabic and Latin characters
            # Supports Arabic (ar) and English (en) for Algerian plates
            self.ocr_reader = easyocr.Reader(['en', 'ar'], gpu=torch.cuda.is_available())
            
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
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Denoise using bilateral filter
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(denoised, (3, 3), 0)
            
            return blurred

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
            # processed_image = self.preprocess_image(image)
            processed_image = image
            
            # Run YOLO detection
            license_plate_detections = self.detection_model(processed_image, conf=self.detection_confidence)[0]

            # detect license plates
            license_plates = []
            for box in license_plate_detections.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = box.conf[0].cpu().numpy()

                license_plates.append([x1, y1, x2, y2, confidence])

            detections = []

            if len(license_plates) > 0:
                tracked_plates = self.tracker.update(np.asarray(license_plates))

                for license_plate in tracked_plates:
                    x1, y1, x2, y2, id = license_plate
                    ious = [
                        max(0, min(x2, dx2) - max(x1, dx1)) *
                        max(0, min(y2, dy2) - max(y1, dy1)) /
                        ((x2 - x1)*(y2 - y1) + (dx2 - dx1)*(dy2 - dy1) -
                         max(0, min(x2, dx2) - max(x1, dx1)) *
                         max(0, min(y2, dy2) - max(y1, dy1)) + 1e-6)
                        for dx1, dy1, dx2, dy2, _ in license_plates
                    ]
                    confidence = license_plates[np.argmax(ious)][4] if len(ious) else 0.0

                    detections.append({
                        'id': id,
                        'bbox': tuple(map(int, (x1, y1, x2, y2))),
                        'confidence': float(confidence),
                        'width': x2 - x1,
                        'height': y2 - y1
                        })
            logger.info(f"Detected {len(detections)} license plates")
            return detections
            
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

            thresh =  cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                35, 2
            )

            # Morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Apply median filter to reduce noise
            filtered = cv2.medianBlur(cleaned, 3)

            # TODO: deskew plate

            cv2.imshow("plate", filtered)
            return filtered

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
            
            # Try EasyOCR first (better for Arabic characters)
            easyocr_results = self.ocr_reader.readtext(enhanced_image)

            # Process EasyOCR results
            if easyocr_results:
                # Get the result with highest confidence
                best_result = max(easyocr_results, key=lambda x: x[2])
                text, confidence = best_result[1], best_result[2]

                # Clean and normalize text
                cleaned_text = self._clean_plate_text(text)

                if confidence >= self.ocr_confidence_threshold and self._validate_plate_text(cleaned_text):
                    return {
                        'text': cleaned_text,
                        'confidence': confidence,
                        'method': 'easyocr',
                        'raw_text': text
                    }

            # Fallback to Tesseract OCR
            tesseract_text = pytesseract.image_to_string(
                enhanced_image, 
                config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ).strip()

            if tesseract_text:
                cleaned_text = self._clean_plate_text(tesseract_text)

                if self._validate_plate_text(tesseract_text):
                    return {
                        'text': cleaned_text,
                        'confidence': self.ocr_confidence_threshold - 0.1,
                        'method': 'tesseract',
                        'raw_text': tesseract_text
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
    
    def process_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Complete pipeline: detect plates and recognize text.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List[Dict]: List of processed plate detections with text recognition
        """
        try:
            start_time = datetime.now()
            
            # Detect license plates
            detections = self.detect_license_plates(image)
            
            results = []
            for detection in detections:
                # Extract plate ROI
                plate_roi = self.extract_plate_roi(image, detection['bbox'])
                
                # Recognize text
                ocr_result = self.recognize_plate_text(plate_roi, detection['id'])

                logger.info(f"LicensePlate: {ocr_result}")
                
                # Combine detection and OCR results
                result = {
                    'detection': detection,
                    'ocr': ocr_result,
                    'overall_confidence': (detection['confidence'] + ocr_result['confidence']) / 2,
                    'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
                }
                
                results.append(result)
            
            if results:
                logger.info(f"Processed {len(results)} plates in {results[0]['processing_time_ms']:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return []
    
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

class VideoProcessor:
    """
    Video processing class for handling video streams and files.
    Supports RTSP streams, video files, and real-time processing.
    """
    
    def __init__(self, plate_processor: LicensePlateProcessor):
        """
        Initialize video processor.
        
        Args:
            plate_processor: LicensePlateProcessor instance
        """
        self.plate_processor = plate_processor
        self.cap = None
        self.frame_count = 0
        
    def open_stream(self, stream_url: str) -> bool:
        """
        Open video stream (RTSP, HTTP, or file).
        
        Args:
            stream_url: URL or path to video stream
            
        Returns:
            bool: True if stream opened successfully
        """
        try:
            self.cap = cv2.VideoCapture(stream_url)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open stream: {stream_url}")
                return False
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info(f"Successfully opened stream: {stream_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening stream: {e}")
            return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read next frame from video stream.
        
        Returns:
            np.ndarray: Frame data or None if no frame available
        """
        try:
            if self.cap is None:
                return None
            
            ret, frame = self.cap.read()
            if ret:
                self.frame_count += 1
                return frame
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None

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

    
    def process_video_stream(self, stream_url: str, callback=None) -> None:
        """
        Process video stream continuously.
        
        Args:
            stream_url: URL or path to video stream
            callback: Optional callback function for processing results
        """
        try:
            if not self.open_stream(stream_url):
                return
            
            logger.info(f"Starting video stream processing: {stream_url}")
            
            while True:
                frame = self.read_frame()
                if frame is None:
                    break
                
                # Process frame for license plates
                results = self.plate_processor.process_image(frame)
                annotated_frame = self.annotate_frame(frame, results)
                
                # Call callback if provided
                if callback and results:
                    callback(results, frame, self.frame_count)
                
                # Break on 'q' key press (for testing)
                cv2.imshow("frame", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
        except Exception as e:
            logger.error(f"Error processing video stream: {e}")
        finally:
            self.close_stream()
    
    def close_stream(self):
        """Close video stream."""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            logger.info("Video stream closed")
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Get video stream information.
        
        Returns:
            Dict: Stream properties
        """
        if self.cap is None:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'frame_count': self.frame_count,
            'is_opened': self.cap.isOpened()
        }
