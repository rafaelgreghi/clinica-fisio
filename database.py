import streamlit as st
from supabase import create_client
import bcrypt
from datetime import datetime, date

# ====================== CONFIGURAÇÃO SUPABASE ======================
SUPABASE_URL = "https://ejsfeguzonfbncyjlbxt.supabase.co"
SUPABASE_KEY = "sb_publishable_TFC-NDkSKil5bB-Za1TSSQ_UXIjGyLt"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """Cria o usuário admin se não existir"""
    supabase = get_supabase()
    try:
        result = supabase.table("users").select("id").eq("username", "admin").execute()
        if not result.data:
            password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            supabase.table("users").insert({
                "name": "Administrador",
                "username": "admin",
                "password_hash": password_hash,
                "role": "admin"
            }).execute()
            print("Usuário admin criado → login: admin | senha: admin123")
    except Exception as e:
        print(f"Aviso init_db: {e}")

# ====================== USUÁRIOS ======================

def create_user(name, username, password, role="professional", phone=None):
    supabase = get_supabase()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        supabase.table("users").insert({
            "name": name,
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "phone": phone
        }).execute()
        return True, "Usuário criado com sucesso"
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, "Nome de usuário já existe"
        return False, str(e)

def authenticate_user(username, password):
    supabase = get_supabase()
    try:
        result = supabase.table("users").select("*").eq("username", username).execute()
        print("Resultado da busca:", result.data)  # Isso vai aparecer na tela preta
        if result.data:
            user = result.data[0]
            print("Hash no banco:", user.get("password_hash"))
            if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                return user
            else:
                print("Senha não bateu")
        else:
            print("Usuário não encontrado")
    except Exception as e:
        print("Erro:", e)
    return None

def get_all_professionals():
    supabase = get_supabase()
    result = supabase.table("users").select("id, name, username, phone, active").eq("role", "professional").order("name").execute()
    return result.data or []

def get_user_by_id(user_id):
    supabase = get_supabase()
    result = supabase.table("users").select("id, name, username, role, phone, active").eq("id", user_id).execute()
    return result.data[0] if result.data else None

# ====================== PACIENTES ======================

def create_patient(data, created_by):
    supabase = get_supabase()
    data["created_by"] = created_by
    result = supabase.table("patients").insert(data).execute()
    return result.data[0]["id"] if result.data else None

def get_patients(status=None, search=None):
    supabase = get_supabase()
    query = supabase.table("patients").select("*")
    if status:
        query = query.eq("status", status)
    result = query.order("full_name").execute()
    patients = result.data or []
    
    if search:
        search = search.lower()
        patients = [p for p in patients if 
                    search in (p.get("full_name") or "").lower() or
                    search in (p.get("cpf") or "").lower() or
                    search in (p.get("phone") or "").lower()]
    return patients

def get_patient_by_id(patient_id):
    supabase = get_supabase()
    result = supabase.table("patients").select("*").eq("id", patient_id).execute()
    return result.data[0] if result.data else None

def update_patient_status(patient_id, status):
    supabase = get_supabase()
    supabase.table("patients").update({"status": status}).eq("id", patient_id).execute()

def update_patient(patient_id, data):
    supabase = get_supabase()
    supabase.table("patients").update(data).eq("id", patient_id).execute()

# ====================== AGENDAMENTOS ======================

def create_appointment(data):
    supabase = get_supabase()
    result = supabase.table("appointments").insert(data).execute()
    return result.data[0]["id"] if result.data else None

def get_appointments(professional_id=None, date_from=None, date_to=None, status=None):
    supabase = get_supabase()
    query = supabase.table("appointments").select("*, patients(full_name), users(name)")
    
    if professional_id:
        query = query.eq("professional_id", professional_id)
    if date_from:
        query = query.gte("appointment_date", date_from)
    if date_to:
        query = query.lte("appointment_date", date_to)
    if status:
        query = query.eq("status", status)
    
    result = query.order("appointment_date").order("start_time").execute()
    
    appointments = []
    for row in (result.data or []):
        appt = dict(row)
        appt["patient_name"] = row.get("patients", {}).get("full_name") if row.get("patients") else ""
        appt["professional_name"] = row.get("users", {}).get("name") if row.get("users") else ""
        appointments.append(appt)
    return appointments

def update_appointment_status(appointment_id, status):
    supabase = get_supabase()
    supabase.table("appointments").update({"status": status}).eq("id", appointment_id).execute()

# ====================== EVOLUÇÕES ======================

def create_evolution(data):
    supabase = get_supabase()
    result = supabase.table("evolutions").insert(data).execute()
    return result.data[0]["id"] if result.data else None

def get_evolutions_by_patient(patient_id):
    supabase = get_supabase()
    result = supabase.table("evolutions").select("*, users(name)").eq("patient_id", patient_id).order("session_date", desc=True).execute()
    
    evolutions = []
    for row in (result.data or []):
        evo = dict(row)
        evo["professional_name"] = row.get("users", {}).get("name") if row.get("users") else ""
        evolutions.append(evo)
    return evolutions

# ====================== FINANCEIRO ======================

def create_payment(data):
    supabase = get_supabase()
    result = supabase.table("payments").insert(data).execute()
    return result.data[0]["id"] if result.data else None

def get_payments(professional_id=None, date_from=None, date_to=None, status=None):
    supabase = get_supabase()
    query = supabase.table("payments").select("*, patients(full_name), users!payments_professional_id_fkey(name)")
    
    if professional_id:
        query = query.eq("professional_id", professional_id)
    if date_from:
        query = query.gte("payment_date", date_from)
    if date_to:
        query = query.lte("payment_date", date_to)
    if status:
        query = query.eq("status", status)
    
    result = query.order("payment_date", desc=True).execute()
    
    payments = []
    for row in (result.data or []):
        pay = dict(row)
        pay["patient_name"] = row.get("patients", {}).get("full_name") if row.get("patients") else ""
        pay["professional_name"] = row.get("users!payments_professional_id_fkey", {}).get("name") if row.get("users!payments_professional_id_fkey") else ""
        payments.append(pay)
    return payments

def get_financial_summary(date_from=None, date_to=None):
    supabase = get_supabase()
    
    query = supabase.table("payments").select("amount, status, professional_id, users!payments_professional_id_fkey(name)")
    if date_from:
        query = query.gte("payment_date", date_from)
    if date_to:
        query = query.lte("payment_date", date_to)
    
    result = query.execute()
    payments = result.data or []
    
    total_pago = sum(p["amount"] for p in payments if p["status"] == "pago")
    total_pendente = sum(p["amount"] for p in payments if p["status"] == "pendente")
    
    por_prof = {}
    for p in payments:
        prof_id = p.get("professional_id")
        if not prof_id:
            continue
        if prof_id not in por_prof:
            user_data = p.get("users!payments_professional_id_fkey") or {}
            por_prof[prof_id] = {
                "id": prof_id,
                "name": user_data.get("name") or "Sem profissional",
                "total_pago": 0,
                "total_pendente": 0,
                "qtd_lancamentos": 0
            }
        por_prof[prof_id]["qtd_lancamentos"] += 1
        if p["status"] == "pago":
            por_prof[prof_id]["total_pago"] += p["amount"]
        elif p["status"] == "pendente":
            por_prof[prof_id]["total_pendente"] += p["amount"]
    
    return {
        "geral": {
            "total_pago": total_pago,
            "total_pendente": total_pendente,
            "total_lancamentos": len(payments)
        },
        "por_profissional": list(por_prof.values())
    }
