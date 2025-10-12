# Smart Vehicle License Scanner (SVA)

A comprehensive, offline license plate recognition system for real-time vehicle monitoring and management.

## 🎯 Project Overview

**Smart Vehicle License Scanner (SVA)** is designed for:
- **Real-time** license plate detection and recognition
- **100% local processing** (no external APIs)
- **Multi-camera support** (IP/CCTV cameras)
- **Web-based dashboard** for monitoring and management
- **Database integration** for whitelist/blacklist management
- **Modular architecture** for easy integration with barriers/IoT systems

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Docker (optional)

### Backend Setup
```bash
# 1. Clone repository
git clone <your-repo-url>
cd SVA

# 2. Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Setup database (PostgreSQL)
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb license_scanner
sudo -u postgres createuser --interactive

# 5. Run backend
python main.py
```

### Frontend Setup
```bash
# 1. Install Node.js dependencies
cd frontend
npm install

# 2. Start development server
npm start
```

### Docker Setup (Alternative)
```bash
# Run entire stack with Docker
docker-compose up -d
```

## 📋 Current Status

### ✅ Working Components
- **Backend API**: FastAPI server with authentication
- **AI/OCR Pipeline**: YOLO detection + EasyOCR/Tesseract recognition
- **Database Models**: SQLAlchemy ORM models
- **Security**: JWT tokens, password hashing, HMAC
- **Privacy**: 100% local processing, no external APIs

### ❌ Missing Components
- **Database Setup**: PostgreSQL installation and configuration
- **Frontend Development**: Complete React application
- **API Integration**: Image upload and real-time processing
- **Custom AI Models**: Training for Algerian license plates
- **Camera Integration**: RTSP/HTTP camera connections

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.119.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: PyTorch, YOLO, EasyOCR, Tesseract
- **Authentication**: JWT tokens with HMAC
- **Image Processing**: OpenCV, PIL

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Context API
- **HTTP Client**: Axios

### AI/OCR
- **Detection**: YOLOv8 (Ultralytics)
- **OCR**: EasyOCR + Tesseract
- **Languages**: Arabic, English, French
- **Privacy**: 100% local processing

## 📚 Documentation

- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)**: Complete project overview and task breakdown
- **[README.md](README.md)**: Detailed setup and usage instructions

## 🎯 For Interns

### Priority Tasks
1. **Database Setup** (Week 1) - Install PostgreSQL and configure
2. **Frontend Development** (Week 2) - Complete React application
3. **AI Model Training** (Week 3) - Train custom models for Algerian plates
4. **API Integration** (Week 4) - Connect frontend to backend
5. **Testing & Deployment** (Week 5) - Production readiness

### Getting Started
1. Read `PROJECT_DOCUMENTATION.md` for complete overview
2. Follow setup instructions above
3. Start with database setup (most critical)
4. Focus on frontend development (highest impact)

## 🔒 Privacy & Security

- **100% Local Processing**: No external API calls
- **Data Sovereignty**: Images never leave your system
- **Offline Operation**: Works without internet
- **Encrypted Storage**: Database encryption
- **Secure Communication**: HTTPS, JWT tokens

## 📈 Performance Targets

- **Plate Detection**: ≥95% daytime, ≥90% night
- **OCR Recognition**: ≥95% for clean plates
- **Processing Speed**: <1 second per frame
- **Real-time Processing**: 25-30 FPS



## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or support, please contact the project maintainers.
b.imane@proxylan.dz
---

**Status**: Development Phase - Ready for collaboration
**Last Updated**: Oct 2025