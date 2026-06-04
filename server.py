from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import re
import jwt
import bcrypt
import secrets
import httpx
from datetime import datetime, timedelta
from supabase import create_client, Client

# -------------------------
# App Setup
# -------------------------
app = FastAPI(title="4Eyes API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Supabase Setup
# -------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
JWT_SECRET = os.environ.get("JWT_SECRET", "4eyes-secret-key-change-in-production")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")  # <-- ADD YOUR RESEND API KEY TO RAILWAY AS RESEND_API_KEY
APP_URL = os.environ.get("APP_URL", "https://4eyeslux.io")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

# -------------------------
# Models
# -------------------------
class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""
    question_1: str
    answer_1: str
    question_2: str
    answer_2: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PrescriptionRequest(BaseModel):
    right_sph: Optional[float] = 0
    right_cyl: Optional[float] = 0
    right_axis: Optional[int] = 90
    left_sph: Optional[float] = 0
    left_cyl: Optional[float] = 0
    left_axis: Optional[int] = 90
    add_val: Optional[float] = 0

class SettingsRequest(BaseModel):
    brightness: Optional[int] = 100
    scale: Optional[float] = 1.0
    contrast: Optional[float] = 1.0
    spacing: Optional[int] = 0
    line_height: Optional[float] = 1.6
    font_weight: Optional[int] = 400
class SecurityQuestionsRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    answer_1: str
    answer_2: str
    new_password: str

# -------------------------
# Auth Helpers
# -------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def validate_password(password: str) -> Optional[str]:
    if len(password) < 5:
        return "Password must be at least 5 characters long"
    if re.match(r'^(.)\1{4,}$', password):
        return "Password cannot be a single repeating character"
    return None

# -------------------------
# Email Helper
# -------------------------
async def send_verification_email(email: str, name: str, token: str):
    verify_url = f"{APP_URL}/dashboard.html?verify={token}"
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "4Eyes <noreply@4eyeslux.io>",
                "to": [email],
                "subject": "Verify your 4Eyes account",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px; background: #0d0f14; color: #e8eaf0; border-radius: 16px;">
                    <h1 style="font-size: 1.8rem; background: linear-gradient(135deg, #5b8dee, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">4Eyes</h1>
                    <p style="color: #6b7280; margin-bottom: 24px;">Vision Adaptive Display Pro</p>
                    <p>Hi {name or 'there'},</p>
                    <p style="margin: 16px 0;">Thanks for signing up! Click the button below to verify your email address and activate your account.</p>
                    <a href="{verify_url}" style="display: inline-block; background: linear-gradient(135deg, #5b8dee, #a78bfa); color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 500; margin: 16px 0;">Verify Email</a>
                    <p style="color: #6b7280; font-size: 0.82rem; margin-top: 24px;">If you didn't create a 4Eyes account, you can safely ignore this email.</p>
                    <p style="color: #6b7280; font-size: 0.82rem;">This link expires in 24 hours.</p>
                </div>
                """
            }
        )

# -------------------------
# Routes
# -------------------------
@app.get("/")
def root():
    return {"status": "4Eyes API running", "version": "1.0.0"}

@app.post("/auth/signup")
async def signup(data: SignupRequest):
    try:
        # Validate password
        pw_error = validate_password(data.password)
        if pw_error:
            raise HTTPException(status_code=400, detail=pw_error)

        # Validate security questions
        if not data.question_1 or not data.answer_1:
            raise HTTPException(status_code=400, detail="Security question 1 is required")
        if not data.question_2 or not data.answer_2:
            raise HTTPException(status_code=400, detail="Security question 2 is required")
        if data.question_1 == data.question_2:
            raise HTTPException(status_code=400, detail="Please choose two different security questions")

        # Check if user exists
        existing = supabase.table("users").select("*").eq("email", data.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Create user (unverified)
        hashed = hash_password(data.password)
        result = supabase.table("users").insert({
            "email": data.email,
            "password": hashed,
            "name": data.name,
            "verified": False,
            "verification_token": verification_token,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        user = result.data[0]

        # Save security questions
        supabase.table("security_questions").insert({
            "user_id": user["id"],
            "question_1": data.question_1,
            "answer_1": data.answer_1.strip().lower(),
            "question_2": data.question_2,
            "answer_2": data.answer_2.strip().lower()
        }).execute()

        # Create empty prescription
        supabase.table("prescriptions").insert({
            "user_id": user["id"],
            "right_sph": 0, "right_cyl": 0, "right_axis": 90,
            "left_sph": 0, "left_cyl": 0, "left_axis": 90,
            "add_val": 0
        }).execute()

        # Send verification email
        await send_verification_email(data.email, data.name, verification_token)

        return {"message": "Account created. Please check your email to verify your account."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/verify")
def verify_email(token: str):
    try:
        result = supabase.table("users").select("*").eq("verification_token", token).execute()
        if not result.data:
            raise HTTPException(status_code=400, detail="Invalid or expired verification link")

        user = result.data[0]
        if user["verified"]:
            return {"message": "Email already verified. You can log in."}

        supabase.table("users").update({
            "verified": True,
            "verification_token": None
        }).eq("id", user["id"]).execute()

        return {"message": "Email verified successfully. You can now log in."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
def login(data: LoginRequest):
    try:
        result = supabase.table("users").select("*").eq("email", data.email).execute()
        if not result.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user = result.data[0]
        if not verify_password(data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Check if email is verified
        if not user.get("verified", False):
            raise HTTPException(status_code=403, detail="Please verify your email before logging in. Check your inbox.")

        token = create_token(user["id"], user["email"])
        return {
            "token": token,
            "user": {"id": user["id"], "email": user["email"], "name": user["name"]}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/resend-verification")
async def resend_verification(data: SecurityQuestionsRequest):
    try:
        result = supabase.table("users").select("*").eq("email", data.email).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="No account found with that email")

        user = result.data[0]
        if user.get("verified", False):
            return {"message": "Email already verified. You can log in."}

        # Generate new token
        new_token = secrets.token_urlsafe(32)
        supabase.table("users").update({"verification_token": new_token}).eq("id", user["id"]).execute()

        await send_verification_email(user["email"], user["name"], new_token)
        return {"message": "Verification email resent. Please check your inbox."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/security-questions")
def get_security_questions(data: SecurityQuestionsRequest):
    try:
        user = supabase.table("users").select("id").eq("email", data.email).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="No account found with that email")

        user_id = user.data[0]["id"]
        questions = supabase.table("security_questions").select("question_1, question_2").eq("user_id", user_id).execute()

        if not questions.data:
            raise HTTPException(status_code=404, detail="No security questions found for this account")

        return {
            "question_1": questions.data[0]["question_1"],
            "question_2": questions.data[0]["question_2"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest):
    try:
        pw_error = validate_password(data.new_password)
        if pw_error:
            raise HTTPException(status_code=400, detail=pw_error)

        user_result = supabase.table("users").select("id, password").eq("email", data.email).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="No account found with that email")

        user = user_result.data[0]
        user_id = user["id"]

        questions = supabase.table("security_questions").select("*").eq("user_id", user_id).execute()
        if not questions.data:
            raise HTTPException(status_code=404, detail="No security questions found")

        q = questions.data[0]
        if data.answer_1.strip().lower() != q["answer_1"]:
            raise HTTPException(status_code=401, detail="Incorrect answer to question 1")
        if data.answer_2.strip().lower() != q["answer_2"]:
            raise HTTPException(status_code=401, detail="Incorrect answer to question 2")

        if verify_password(data.new_password, user["password"]):
            raise HTTPException(status_code=400, detail="New password cannot be the same as your current password")

        new_hash = hash_password(data.new_password)
        supabase.table("users").update({"password": new_hash}).eq("id", user_id).execute()

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prescription")
def get_prescription(user=Depends(verify_token)):
    try:
        result = supabase.table("prescriptions").select("*").eq("user_id", user["user_id"]).execute()
        if not result.data:
            return {}
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prescription")
def save_prescription(data: PrescriptionRequest, user=Depends(verify_token)):
    try:
        existing = supabase.table("prescriptions").select("*").eq("user_id", user["user_id"]).execute()
        payload = {
            "user_id": user["user_id"],
            "right_sph": data.right_sph, "right_cyl": data.right_cyl, "right_axis": data.right_axis,
            "left_sph": data.left_sph, "left_cyl": data.left_cyl, "left_axis": data.left_axis,
            "add_val": data.add_val, "updated_at": datetime.utcnow().isoformat()
        }
        if existing.data:
            supabase.table("prescriptions").update(payload).eq("user_id", user["user_id"]).execute()
        else:
            supabase.table("prescriptions").insert(payload).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
def get_settings(user=Depends(verify_token)):
    try:
        result = supabase.table("settings").select("*").eq("user_id", user["user_id"]).execute()
        if not result.data:
            return {"brightness": 100, "scale": 1.0, "contrast": 1.0, "spacing": 0, "line_height": 1.6, "font_weight": 400}
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings")
def save_settings(data: SettingsRequest, user=Depends(verify_token)):
    try:
        existing = supabase.table("settings").select("*").eq("user_id", user["user_id"]).execute()
        payload = {
                "user_id": user["user_id"],
                "brightness": data.brightness,
                "scale": data.scale,
                "contrast": data.contrast,
                "spacing": data.spacing,
                "line_height": data.line_height,
                "font_weight": data.font_weight,
                "updated_at": datetime.utcnow().isoformat()
        }
        if existing.data:
            supabase.table("settings").update(payload).eq("user_id", user["user_id"]).execute()
        else:
            supabase.table("settings").insert(payload).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/extension/settings")
def extension_settings(user=Depends(verify_token)):
    try:
        settings = supabase.table("settings").select("*").eq("user_id", user["user_id"]).execute()
        prescription = supabase.table("prescriptions").select("*").eq("user_id", user["user_id"]).execute()
        return {
            "settings": settings.data[0] if settings.data else {},
            "prescription": prescription.data[0] if prescription.data else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))