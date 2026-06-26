
# STUDYNOVA RENDER DEPLOYMENT GUIDE
## Persistent Database (PostgreSQL) + Cloudinary Setup

---

## STEP 1: PREPARE YOUR REPOSITORY
Make sure these files are committed:
- `app.py` (already has PostgreSQL support!)
- `requirements.txt` (includes psycopg2-binary)
- `render.yaml` (we just created this)

---

## STEP 2: DEPLOY TO RENDER
1. Go to [Render.com](https://render.com) and sign in
2. Click **New + → Web Service**
3. Connect your GitHub repository
4. Use the settings from `render.yaml`:
   - **Name:** `studynova`
   - **Runtime:** Python 3
   - **Branch:** main
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
5. Click **Create Web Service**

---

## STEP 3: ADD PERSISTENT POSTGRESQL DATABASE
1. In Render dashboard, go to your Web Service
2. Click **New + → PostgreSQL**
3. Name: `studynova-db`
4. Plan: Free
5. Click **Create Database**

---

## STEP 4: SET UP ENVIRONMENT VARIABLES
Go to your Web Service → **Environment → Environment Variables** and add:
| Key | Value | Notes |
|-----|-------|-------|
| `CLOUDINARY_CLOUD_NAME` | [Your Cloudinary Cloud Name] | From [Cloudinary Dashboard](https://cloudinary.com) |
| `CLOUDINARY_API_KEY` | [Your Cloudinary API Key] | |
| `CLOUDINARY_API_SECRET` | [Your Cloudinary API Secret] | |
| `STUDYNOVA_ADMIN_EMAIL` | admin@studynova.com | Your admin email |
| `STUDYNOVA_ADMIN_PASSWORD` | [Secure admin password] | |
| `STUDYNOVA_ADMIN_NAME` | StudyNova Admin | |
| `DATABASE_URL` | [Render PostgreSQL Connection String] | Automatically added if you used render.yaml |

---

## STEP 5: VERIFY DEPLOYMENT & TEST DATA PERSISTENCE
1. **Create a Test User** on the deployed site
2. **Upload a Test Note**
3. **Add a Test Team Member** (via Admin Panel)
4. **Restart the Render Service** (Web Service → Manual Deploy → Deploy latest commit)
5. Verify all test data is still present! 🎉

---

## STEP 6: DONE!
Your StudyNova deployment now uses **persistent PostgreSQL** for data and **Cloudinary** for files! No more ephemeral storage issues!
