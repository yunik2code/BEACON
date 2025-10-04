# 🛰️ BEACON - Satellite Booking System

A comprehensive satellite booking and management system with an Electron-based frontend and Flask backend.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- **npm** (comes with Node.js) or **yarn**
- **Python** (v3.8 or higher) - [Download](https://www.python.org/)
- **pip** (comes with Python)
- **Git** - [Download](https://git-scm.com/)

### Verify Installation

```bash
node --version
npm --version
python3 --version
pip3 --version
```

---

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yunik2code/BEACON.git
cd BEACON
```

---

## 🐍 Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd app_backend
```

### Step 2: Create Virtual Environment

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the `app_backend` directory:

Edit `.env` and add your configurations:

```env
SECRET_KEY= your secret key(optional)
DATABASE_URL=sqlite:///./satellite_booking.db (or your db)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

### Step 5: Initialize Database

```bash
python main.py
```

The database will be automatically created on first run.

---

## ⚛️ Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd ../app
```

### Step 2: Install Dependencies

```bash
npm install
```

**Note:** This may take a few minutes as it installs Electron and other dependencies.

### Step 3: Add Google Client id

Open main.js in app/main.js and in line 40 change with oauth your client id

```bash
`client_id={Your google client id}`
```


#### Getting Google OAuth Credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure the consent screen if prompted
6. Set application type to **Web application**
7. Add authorized redirect URIs (e.g., `http://localhost:3000/callback`)
8. Copy the Client ID and Client Secret to your `.env` file

---

## 🚀 Running the Application

### Option 1: Run Backend and Frontend Separately

#### Terminal 1 - Start Backend:

```bash
cd app_backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

Backend will run on: `http://localhost:5000`

#### Terminal 2 - Start Frontend:

```bash
cd app
npm start
```

The Electron app will launch automatically.

### Option 2: Development Mode

For frontend development with hot reload:

```bash
cd app
npm run dev
```

---

## 📁 Project Structure

```
BEACON/
├── app/                          # Frontend (Electron + React)
│   ├── node_modules/            # Dependencies (not in git)
│   ├── public/                  # Static assets
│   ├── src/                     # React source code
│   ├── main.js                  # Electron main process
│   ├── preload.js              # Electron preload script
│   ├── package.json            # Frontend dependencies

│
├── app_backend/                 # Backend (Flask + Python)
│   ├── venv/                   # Virtual environment (not in git)
│   ├── __pycache__/            # Python cache (not in git)
│   ├── main.py                 # Flask application
│   ├── requirements.txt        # Python dependencies
│   ├── satellite_booking.db    # SQLite database
│   ├── .env                    # Backend config (not in git)
│
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 🔍 Troubleshooting

### Port Already in Use

If port 5000 or 3000 is already in use:

**Backend:**
Edit `main.py` and change the port:
```python
app.run(debug=True, port=5001)
```

**Frontend:**
Update `REACT_APP_API_URL` in `app/.env` to match the new backend port.

### Module Not Found Errors

**Backend:**
```bash
cd app_backend
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd app
rm -rf node_modules package-lock.json
npm install
```

### Database Issues

If you encounter database errors:

```bash
cd app_backend
rm satellite_booking.db
python main.py  # Will recreate the database
```

### Electron Won't Start

Clear Electron cache:

```bash
cd app
rm -rf node_modules/.cache
npm start
```

### Google OAuth Errors

Ensure:
1. Credentials are correctly set in `.env`
2. Authorized redirect URIs are configured in Google Cloud Console
3. OAuth consent screen is configured

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Authors

- **yunik2code** - [GitHub Profile](https://github.com/yunik2code)

---

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Open an issue on [GitHub Issues](https://github.com/yunik2code/BEACON/issues)
3. Contact the development team

---

## 🎯 Features

- 🛰️ Satellite booking and management
- 👤 User authentication with Google OAuth
- 📊 Real-time availability tracking
- 💾 SQLite database for data persistence
- 🖥️ Cross-platform desktop application (Electron)
- 🎨 Modern, responsive UI
- 🔒 Secure API endpoints

---

**Happy Coding! 🚀**