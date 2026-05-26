from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import re
import jwt
import bcrypt
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
# Routes
# -------------------------
@app.get("/")
def root():
    return {"status": "4Eyes API running", "version": "1.0.0"}

@app.post("/auth/signup")
def signup(data: SignupRequest):
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

        # Create user
        hashed = hash_password(data.password)
        result = supabase.table("users").insert({
            "email": data.email,
            "password": hashed,
            "name": data.name,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        user = result.data[0]
        token = create_token(user["id"], user["email"])

        # Save security questions (answers stored lowercase for case-insensitive matching)
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

        return {
            "token": token,
            "user": {"id": user["id"], "email": user["email"], "name": user["name"]}
        }

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

        token = create_token(user["id"], user["email"])
        return {
            "token": token,
            "user": {"id": user["id"], "email": user["email"], "name": user["name"]}
        }

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
        # Validate new password
        pw_error = validate_password(data.new_password)
        if pw_error:
            raise HTTPException(status_code=400, detail=pw_error)

        # Get user
        user_result = supabase.table("users").select("id, password").eq("email", data.email).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="No account found with that email")

        user = user_result.data[0]
        user_id = user["id"]

        # Get security questions and answers
        questions = supabase.table("security_questions").select("*").eq("user_id", user_id).execute()
        if not questions.data:
            raise HTTPException(status_code=404, detail="No security questions found")

        q = questions.data[0]

        # Verify answers (case-insensitive)
        if data.answer_1.strip().lower() != q["answer_1"]:
            raise HTTPException(status_code=401, detail="Incorrect answer to question 1")
        if data.answer_2.strip().lower() != q["answer_2"]:
            raise HTTPException(status_code=401, detail="Incorrect answer to question 2")

        # Check it's not the same as current password
        if verify_password(data.new_password, user["password"]):
            raise HTTPException(status_code=400, detail="New password cannot be the same as your current password")

        # Update password
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
            return {"brightness": 100, "scale": 1.0, "contrast": 1.0, "spacing": 0, "line_height": 1.6}
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings")
def save_settings(data: SettingsRequest, user=Depends(verify_token)):
    try:
        existing = supabase.table("settings").select("*").eq("user_id", user["user_id"]).execute()
        payload = {
            "user_id": user["user_id"],
            "brightness": data.brightness, "scale": data.scale, "contrast": data.contrast,
            "spacing": data.spacing, "line_height": data.line_height,
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