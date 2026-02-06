"""
Forsa Finance AI Chatbot - Complete with All Features
Branch Locator | Payment Reminders | Product Recommendations | Conversation Memory
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Literal
from datetime import datetime, timedelta
import uuid
import os
import re
import math
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Forsa Finance AI Chatbot",
    description="AI-powered customer service with full feature set",
    version="5.4.0-complete"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Setup
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("gsk_"):
        client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.groq.com/openai/v1")
        AI_ENABLED = True
    else:
        AI_ENABLED = False
        client = None
except ImportError:
    AI_ENABLED = False
    client = None

# ============ DATABASE ============

existing_customers = {
    "user123": {
        "id": "user123",
        "type": "existing",
        "name": "Ahmed Hassan",
        "phone": "+201012345678",
        "email": "ahmed@email.com",
        "language": "ar",
        "credit_limit": 50000,
        "available_credit": 32500,
        "status": "active",
        "location": "Cairo",
        "member_since": "2024-01-15",
        "installments": [
            {
                "id": "inst001",
                "product": "iPhone 15 Pro",
                "merchant": "Dubai Phone",
                "total_amount": 42000,
                "monthly": 3500,
                "remaining": 28000,
                "months_remaining": 8,
                "next_date": (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
                "next_amount": 3500,
                "status": "active"
            },
            {
                "id": "inst002",
                "product": "IKEA Sofa",
                "merchant": "IKEA Egypt",
                "total_amount": 12000,
                "monthly": 1000,
                "remaining": 6000,
                "months_remaining": 6,
                "next_date": (datetime.now() + timedelta(days=13)).strftime("%Y-%m-%d"),
                "next_amount": 1000,
                "status": "active"
            }
        ],
    }
}

new_customer_template = {
    "type": "new",
    "name": None,
    "credit_limit": None,
    "available_credit": 0,
    "status": "prospective",
    "location": "Cairo",
}

# ============ PRODUCT CATALOG ============

PRODUCT_CATALOG = [
    {"name": "iPhone 15 Pro", "category": "electronics", "price": 42000, "merchant": "Dubai Phone", "popularity": 95, "image": "📱"},
    {"name": "Samsung Galaxy S24 Ultra", "category": "electronics", "price": 38000, "merchant": "Dubai Phone", "popularity": 90, "image": "📱"},
    {"name": "MacBook Air M3", "category": "electronics", "price": 45000, "merchant": "Dubai Phone", "popularity": 88, "image": "💻"},
    {"name": "iPad Pro 12.9", "category": "electronics", "price": 28000, "merchant": "Dubai Phone", "popularity": 85, "image": "📱"},
    {"name": "PlayStation 5", "category": "gaming", "price": 18500, "merchant": "Dubai Phone", "popularity": 92, "image": "🎮"},
    {"name": "LG 65\" OLED TV", "category": "electronics", "price": 32000, "merchant": "Dubai Phone", "popularity": 80, "image": "📺"},
    {"name": "IKEA Sofa", "category": "furniture", "price": 12000, "merchant": "IKEA Egypt", "popularity": 75, "image": "🛋️"},
    {"name": "IKEA Bedroom Set", "category": "furniture", "price": 25000, "merchant": "IKEA Egypt", "popularity": 70, "image": "🛏️"},
    {"name": "Toshiba Washing Machine", "category": "appliances", "price": 8500, "merchant": "Dubai Phone", "popularity": 65, "image": "🧺"},
    {"name": "Samsung Refrigerator", "category": "appliances", "price": 15000, "merchant": "Dubai Phone", "popularity": 72, "image": "❄️"},
    {"name": "Dell XPS 15", "category": "electronics", "price": 35000, "merchant": "Dubai Phone", "popularity": 78, "image": "💻"},
    {"name": "AirPods Pro 2", "category": "accessories", "price": 6500, "merchant": "Dubai Phone", "popularity": 88, "image": "🎧"},
]

# ============ BRANCH DATA ============

FORSA_BRANCHES = [
    {"name": "City Center Alexandria", "type": "Booth", "city": "Alexandria", 
     "hours": "10 AM - 10 PM (Weekdays), 10 AM - 11 PM (Weekend)", 
     "address": "City Center Alexandria - Gate 3 - Front of Tradeline & Costa",
     "lat": 31.2001, "lng": 29.9187, "phone": "03-1234567"},
    
    {"name": "City Stars", "type": "Booth", "city": "Cairo", 
     "hours": "10 AM - 10 PM (Weekdays), 10 AM - 11 PM (Weekend)", 
     "address": "City Stars Mall - Gate 6, Nasr City",
     "lat": 30.0561, "lng": 31.3462, "phone": "02-1234567"},
    
    {"name": "Mall of Egypt", "type": "Booth", "city": "6th of October", 
     "hours": "10 AM - 10 PM (Weekdays), 10 AM - 11 PM (Weekend)", 
     "address": "Mall of Egypt - Gate C1, between Beanos & LC Waikiki",
     "lat": 29.9708, "lng": 30.9776, "phone": "02-1234568"},
    
    {"name": "City Center Almaza", "type": "Booth", "city": "Cairo", 
     "hours": "10 AM - 10 PM (Weekdays), 10 AM - 11 PM (Weekend)", 
     "address": "Masr El Gedida - City Center Almaza - Front of Mazaya store",
     "lat": 30.1124, "lng": 31.3439, "phone": "02-1234569"},
    
    {"name": "Cairo Festival City", "type": "Booth", "city": "Cairo", 
     "hours": "10 AM - 10 PM (Weekdays), 10 AM - 11 PM (Weekend)", 
     "address": "Cairo Festival City Mall - Second Floor - LC Waikiki Gate",
     "lat": 30.0313, "lng": 31.4116, "phone": "02-1234570"},
    
    {"name": "Carrefour Maadi", "type": "Carrefour", "city": "Cairo", 
     "hours": "1 PM - 9 PM (Daily)", 
     "address": "Maadi City Center",
     "lat": 29.9602, "lng": 31.2569, "phone": "02-1234571"},
    
    {"name": "Carrefour Alexandria", "type": "Carrefour", "city": "Alexandria", 
     "hours": "1 PM - 9 PM (Daily)", 
     "address": "City Center Alexandria",
     "lat": 31.2001, "lng": 29.9187, "phone": "03-1234572"},
    
    {"name": "Drive Kattamia", "type": "Drive Branch", "city": "Cairo", 
     "hours": "9 AM - 5:30 PM (Sun-Thu), Closed (Fri-Sat)", 
     "address": "7 Exhibition Area, Kattamia",
     "lat": 29.9915, "lng": 31.4056, "phone": "02-1234573"},
    
    {"name": "Drive Alexandria", "type": "Drive Branch", "city": "Alexandria", 
     "hours": "9 AM - 5:30 PM (Sun-Thu), Closed (Fri-Sat)", 
     "address": "Roushdy - El Horreya Road, opposite London Boutique",
     "lat": 31.2156, "lng": 29.9553, "phone": "03-1234574"},
    
    {"name": "Dubai Phone Dokki", "type": "Dubai Phone", "city": "Giza", 
     "hours": "2 PM - 10 PM (Daily)", 
     "address": "Mossadak Street, Dokki",
     "lat": 30.0395, "lng": 31.2025, "phone": "02-1234575"},
]

# ============ CONVERSATION MEMORY ============

class ConversationMemory:
    def __init__(self):
        self.sessions = {}
    
    def get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "user_type": None,
                "user_id": None,
                "context": {
                    "last_intent": None,
                    "awaiting_input": None,
                    "collected_data": {},
                    "conversation_stage": "greeting",
                    "last_branch_city": "Cairo"
                },
                "history": [],
            }
        return self.sessions[session_id]
    
    def update_context(self, session_id, key, value):
        session = self.get_session(session_id)
        session["context"][key] = value
    
    def add_to_history(self, session_id, role, message, intent=None):
        session = self.get_session(session_id)
        session["history"].append({
            "role": role,
            "message": message,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        if len(session["history"]) > 10:
            session["history"] = session["history"][-10:]

memory = ConversationMemory()

# ============ SMART FEATURES CLASSES ============

class BranchLocator:
    def __init__(self):
        self.city_centers = {
            "Cairo": {"lat": 30.0444, "lng": 31.2357},
            "Alexandria": {"lat": 31.2001, "lng": 29.9187},
            "Giza": {"lat": 30.0131, "lng": 31.2089},
            "6th of October": {"lat": 29.9708, "lng": 30.9776},
        }
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def find_nearest(self, city="Cairo", limit=3):
        center = self.city_centers.get(city, self.city_centers["Cairo"])
        
        branches_with_dist = []
        for b in FORSA_BRANCHES:
            dist = self.calculate_distance(center["lat"], center["lng"], b["lat"], b["lng"])
            branches_with_dist.append({**b, "distance": dist})
        
        branches_with_dist.sort(key=lambda x: x["distance"])
        return branches_with_dist[:limit]
    
    def format_response(self, branches, lang, city="Cairo"):
        if lang == "ar":
            response = f"🏪 **أقرب {len(branches)} فروع ليك في {city}:**\n\n"
            for i, b in enumerate(branches, 1):
                maps_url = f"https://www.google.com/maps?q={b['lat']},{b['lng']}"
                response += f"{i}. **{b['name']}** 📍\n"
                response += f"   المسافة: {b['distance']:.1f} كم\n"
                response += f"   📌 {b['address']}\n"
                response += f"   🕐 {b['hours']}\n"
                response += f"   📞 {b['phone']}\n"
                response += f"   🗺️ [افتح الخريطة]({maps_url})\n\n"
        else:
            response = f"🏪 **{len(branches)} Nearest Branches in {city}:**\n\n"
            for i, b in enumerate(branches, 1):
                maps_url = f"https://www.google.com/maps?q={b['lat']},{b['lng']}"
                response += f"{i}. **{b['name']}** 📍\n"
                response += f"   Distance: {b['distance']:.1f} km\n"
                response += f"   📌 {b['address']}\n"
                response += f"   🕐 {b['hours']}\n"
                response += f"   📞 {b['phone']}\n"
                response += f"   🗺️ [Open Map]({maps_url})\n\n"
        
        return response

class PaymentReminder:
    def get_reminders(self, user_data, lang):
        installments = user_data.get("installments", [])
        if not installments:
            return "✅ مفيش عليك أقساط حالياً!" if lang == "ar" else "✅ You have no pending installments!"
        
        today = datetime.now()
        
        if lang == "ar":
            response = "⏰ **تذكيرات الدفع:**\n\n"
        else:
            response = "⏰ **Payment Reminders:**\n\n"
        
        for inst in installments:
            next_date = datetime.strptime(inst["next_date"], "%Y-%m-%d")
            days_left = (next_date - today).days
            
            # Status emoji
            if days_left < 0:
                status = "🔴 متأخر"
                status_en = "🔴 Overdue"
            elif days_left == 0:
                status = "🔴 مستحق اليوم"
                status_en = "🔴 Due today"
            elif days_left <= 3:
                status = f"🟡 خلال {days_left} أيام"
                status_en = f"🟡 In {days_left} days"
            else:
                status = f"🟢 {days_left} يوم"
                status_en = f"🟢 {days_left} days"
            
            if lang == "ar":
                response += f"**{inst['product']}** {inst.get('image', '')}\n"
                response += f"💰 {inst['next_amount']:,} جنيه\n"
                response += f"📅 {inst['next_date']} ({status})\n"
                response += f"🏪 {inst['merchant']}\n"
                response += f"⏱️ متبقي {inst['months_remaining']} أشهر\n\n"
            else:
                response += f"**{inst['product']}** {inst.get('image', '')}\n"
                response += f"💰 {inst['next_amount']:,} EGP\n"
                response += f"📅 {inst['next_date']} ({status_en})\n"
                response += f"🏪 {inst['merchant']}\n"
                response += f"⏱️ {inst['months_remaining']} months remaining\n\n"
        
        # Add payment method reminder
        if lang == "ar":
            response += "💳 **طرق الدفع:**\nفوري: 70975 | تطبيق فُرصة | بنك أونلاين"
        else:
            response += "💳 **Payment Methods:**\nFawry: 70975 | Forsa App | Online Banking"
        
        return response

class ProductRecommender:
    def recommend(self, available_credit, lang, category=None):
        # Filter by available credit (80% max)
        max_price = available_credit * 0.8
        affordable = [p for p in PRODUCT_CATALOG if p["price"] <= max_price]
        
        # Filter by category if specified
        if category:
            affordable = [p for p in affordable if p["category"] == category]
        
        # Sort by popularity
        affordable.sort(key=lambda x: x["popularity"], reverse=True)
        top_products = affordable[:4]
        
        if not top_products:
            if lang == "ar":
                return f"💳 رصيدك المتاح ({available_credit:,} جنيه) لا يسمح بشراء منتجات حالياً.\n\nزود رصيدك أو سدد أقساطك الحالية أولاً."
            else:
                return f"💳 Your available credit ({available_credit:,} EGP) is too low for purchases.\n\nIncrease your credit or pay off current installments first."
        
        if lang == "ar":
            response = f"🛍️ **منتجات مقترحة ليك (رصيدك: {available_credit:,} جنيه):**\n\n"
            for p in top_products:
                monthly_12 = (p["price"] / 12) + 20
                monthly_6 = (p["price"] / 6) + 20
                response += f"{p['image']} **{p['name']}**\n"
                response += f"   💵 {p['price']:,} جنيه\n"
                response += f"   🏪 {p['merchant']}\n"
                response += f"   💳 {monthly_12:,.0f} جنيه/شهر (12 شهر)\n"
                response += f"   أو {monthly_6:,.0f} جنيه/شهر (6 أشهر)\n\n"
            
            response += "🧮 **عايز تحسب قسط بدقة؟** قولي 'احسب' والمبلغ!"
        else:
            response = f"🛍️ **Recommended for You (Credit: {available_credit:,} EGP):**\n\n"
            for p in top_products:
                monthly_12 = (p["price"] / 12) + 20
                monthly_6 = (p["price"] / 6) + 20
                response += f"{p['image']} **{p['name']}**\n"
                response += f"   💵 {p['price']:,} EGP\n"
                response += f"   🏪 {p['merchant']}\n"
                response += f"   💳 {monthly_12:,.0f} EGP/month (12 months)\n"
                response += f"   or {monthly_6:,.0f} EGP/month (6 months)\n\n"
            
            response += "🧮 **Want exact calculation?** Say 'calculate' and the amount!"
        
        return response

class SmartCalculator:
    def calculate(self, amount, months, lang):
        annual_rate = 0.15
        total_interest = amount * annual_rate * (months / 12)
        total_amount = amount + total_interest
        monthly_payment = total_amount / months
        total_monthly = monthly_payment + 20
        
        if lang == "ar":
            return f"""🧮 **نتيجة الحساب:**

💰 المبلغ: {amount:,.0f} جنيه
📅 المدة: {months} شهر
📊 الفائدة (15%): {total_interest:,.0f} جنيه

💵 **القسط الشهري: {monthly_payment:,.0f} جنيه**
➕ رسوم التحصيل: 20 جنيه
✅ **الإجمالي: {total_monthly:,.0f} جنيه/شهر**

💳 السعر الكلي: {total_amount:,.0f} جنيه

**عايز تحسب لمبلغ تاني؟**"""
        else:
            return f"""🧮 **Calculation Result:**

💰 Amount: {amount:,.0f} EGP
📅 Duration: {months} months
📊 Interest (15%): {total_interest:,.0f} EGP

💵 **Monthly Payment: {monthly_payment:,.0f} EGP**
➕ Collection Fee: 20 EGP
✅ **Total: {total_monthly:,.0f} EGP/month**

💳 Total Cost: {total_amount:,.0f} EGP

**Want to calculate another amount?**"""

# Initialize features
branch_locator = BranchLocator()
payment_reminder = PaymentReminder()
recommender = ProductRecommender()
calculator = SmartCalculator()

# ============ AI ENGINE ============

class ConversationalAI:
    def __init__(self):
        self.follow_up_handlers = {
            "eligibility_age": self.handle_eligibility_age,
            "eligibility_salary": self.handle_eligibility_salary,
            "eligibility_type": self.handle_eligibility_type,
            "calculator_amount": self.handle_calculator_amount,
            "calculator_months": self.handle_calculator_months,
            "phone_change": self.handle_phone_change,
            "email_change": self.handle_email_change,
            "branch_city": self.handle_branch_city,
        }
    
    def detect_language(self, text):
        arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهويىءآأإؤةئ')
        for char in text:
            if char in arabic_chars:
                return "ar"
        return "en"
    
    def detect_intent(self, message):
        msg_lower = message.lower().strip()
        
        # EXACT MATCHES for quick replies
        exact_matches = {
            # NEW CUSTOMER
            "eligibility": [
                "check eligibility", "فحص التأهل", "عايز أعرف لو مؤهل", "هل أنا مؤهل",
                "membership", "اشترك", "انضم", "join", "تسجيل", "register",
                "📝 check eligibility", "📝 فحص التأهل", "📝 عايز أعرف لو مؤهل"
            ],
            "documents": [
                "required documents", "الأوراق المطلوبة", "ايه الأوراق", "محتاج ايه اوراق",
                "documents", "اوراق", "مستندات", "مطلوب ايه", "ايه المطلوب",
                "📋 required documents", "📋 الأوراق المطلوبة", "📋 ايه الأوراق"
            ],
            "calculate": [
                "calculate installment", "احسب قسط", "حاسبة", "calculator",
                "🧮 calculate installment", "🧮 احسب قسط", "calculate", "احسب"
            ],
            
            # EXISTING CUSTOMER
            "balance": [
                "my balance", "رصيدي", "credit", "available", "رصيد", "فلوسي",
                "💳 my balance", "💳 رصيدي", "💳 عايز أعرف رصيدي"
            ],
            "installments": [
                "my installments", "اقساطي", "payments", "دفعات", "عليا كام",
                "📋 my installments", "📋 اقساطي", "📋 عايز أعرف اقساطي"
            ],
            "reminders": [
                "payment reminders", "تذكيرات الدفع", "متى القسط", "موعد الدفع",
                "reminders", "تذكير", "القسط الجاي", "next payment",
                "⏰ payment reminders", "⏰ تذكيرات الدفع", "⏰ متى القسط الجاي"
            ],
            "recommendations": [
                "recommend products", "اقترح منتجات", "عايز اشتري", "what can i buy",
                "recommend", "اقتراح", "suggest", "products", "منتجات",
                "🛍️ recommend products", "🛍️ اقترح منتجات", "🛍️ عايز اشتري حاجة"
            ],
            
            # BOTH
            "branch": [
                "find branch", "nearest branch", "أقرب فرع", "فروع", "branch",
                "🏪 find branch", "🏪 أقرب فرع", "🏪 فين الفرع", "location", "مكان"
            ],
            "change_phone": ["change phone", "غير رقم", "رقم جديد", "تغيير الهاتف"],
            "change_email": ["change email", "غير ايميل", "ايميل جديد", "تغيير الايميل"],
        }
        
        for intent, phrases in exact_matches.items():
            if any(phrase.lower() in msg_lower or msg_lower in phrase.lower() for phrase in phrases):
                return intent
        
        # Input patterns
        if re.search(r'\b\d{1,2}\b', msg_lower) and any(x in msg_lower for x in ["سنة", "year", "سنه"]):
            return "age_input"
        if re.search(r'\d{4,6}', msg_lower) and any(x in msg_lower for x in ["جنيه", "egp", "راتب", "salary"]):
            return "salary_input"
        if any(x in msg_lower for x in ["موظف", "employee", "business", "صاحب عمل"]):
            return "employment_type_input"
        
        return "general"
    
    def generate_response(self, message, session, user_data=None):
        lang = self.detect_language(message)
        intent = self.detect_intent(message)
        context = session["context"]
        
        print(f"DEBUG: Message='{message}', Intent='{intent}', Awaiting='{context.get('awaiting_input')}'")
        
        # CHECK FOLLOW-UP
        awaiting = context.get("awaiting_input")
        if awaiting and awaiting in self.follow_up_handlers:
            return self.follow_up_handlers[awaiting](message, lang, context, user_data)
        
        # ========== NEW CUSTOMER INTENTS ==========
        if intent == "eligibility":
            context["awaiting_input"] = "eligibility_age"
            context["collected_data"] = {}
            if lang == "ar":
                return "📋 **فحص التأهل للعضوية:**\n\n**الخطوة 1/3: عمرك كام سنة؟** (21-60)"
            else:
                return "📋 **Eligibility Check:**\n\n**Step 1/3: How old are you?** (21-60)"
        
        elif intent == "documents":
            if lang == "ar":
                return """📋 **الأوراق المطلوبة للتفعيل:**

1️⃣ **بطاقة شخصية سارية** (أصل، مش صورة)
2️⃣ **إثبات دخل** (مفردات مرتب أو سجل تجاري)
3️⃣ **مستندات إضافية** (اختياري - تزيد الحد)
   - عضوية نادي أو رخصة سيارة

❌ **مش بنقبل:** التوكيل، عقد البيع

**عايز تعرف أقرب فرع؟ اضغط 🏪**"""
            else:
                return """📋 **Required Documents:**

1️⃣ **Valid National ID** (original, not copy)
2️⃣ **Income Proof** (salary statement or commercial record)
3️⃣ **Additional** (optional - increases limit)
   - Club membership or car license

❌ **Not accepted:** Proxy, sales contract

**Want nearest branch? Click 🏪**"""
        
        elif intent == "calculate":
            context["awaiting_input"] = "calculator_amount"
            context["collected_data"] = {}
            if lang == "ar":
                return "🧮 **حاسبة الأقساط**\n\n**أدخل المبلغ (جنيه):**"
            else:
                return "🧮 **Installment Calculator**\n\n**Enter amount (EGP):**"
        
        # ========== EXISTING CUSTOMER INTENTS ==========
        elif intent == "balance" and user_data and user_data.get("type") == "existing":
            available = user_data.get("available_credit", 0)
            total = user_data.get("credit_limit", 0)
            used = total - available
            name = user_data.get("name", "")
            
            if lang == "ar":
                return f"""👋 أهلا {name}! 

💳 **رصيدك:**
• المتاح: **{available:,}** جنيه
• الحد الكلي: {total:,} جنيه
• المستخدم: {used:,} جنيه

**عايز تشوف منتجات تناسب رصيدك؟ اضغط 🛍️**"""
            else:
                return f"""👋 Hi {name}!

💳 **Your Balance:**
• Available: **{available:,}** EGP
• Total Limit: {total:,} EGP
• Used: {used:,} EGP

**Want to see products for your credit? Click 🛍️**"""
        
        elif intent == "installments" and user_data and user_data.get("type") == "existing":
            insts = user_data.get("installments", [])
            if not insts:
                return "✅ مفيش أقساط!" if lang == "ar" else "✅ No installments!"
            
            if lang == "ar":
                response = f"📋 **أقساطك يا {user_data.get('name', '')}:**\n\n"
                for inst in insts:
                    response += f"• **{inst['product']}**: {inst['next_amount']:,} جنيه يوم {inst['next_date']}\n"
                response += f"\n**⏰ عايز تذكير بالمواعيد؟ اضغط ⏰**"
            else:
                response = f"📋 **Your Installments, {user_data.get('name', '')}:**\n\n"
                for inst in insts:
                    response += f"• **{inst['product']}**: {inst['next_amount']:,} EGP on {inst['next_date']}\n"
                response += f"\n**⏰ Want payment reminders? Click ⏰**"
            return response
        
        elif intent == "reminders" and user_data and user_data.get("type") == "existing":
            return payment_reminder.get_reminders(user_data, lang)
        
        elif intent == "recommendations" and user_data and user_data.get("type") == "existing":
            available = user_data.get("available_credit", 0)
            return recommender.recommend(available, lang)
        
        # ========== BOTH MODES ==========
        elif intent == "branch":
            city = user_data.get("location", "Cairo") if user_data else "Cairo"
            branches = branch_locator.find_nearest(city, 3)
            return branch_locator.format_response(branches, lang, city)
        
        elif intent == "change_phone":
            context["awaiting_input"] = "phone_change"
            if lang == "ar":
                return "📱 **تغيير رقم التليفون**\n\nأرسل الرقم الجديد:"
            else:
                return "📱 **Change Phone Number**\n\nSend new number:"
        
        elif intent == "change_email":
            context["awaiting_input"] = "email_change"
            if lang == "ar":
                return "📧 **تغيير الإيميل**\n\nأرسل الإيميل الجديد:"
            else:
                return "📧 **Change Email**\n\nSend new email:"
        
        # ========== DEFAULT GREETINGS ==========
        else:
            if user_data and user_data.get("type") == "existing":
                name = user_data.get("name", "")
                if lang == "ar":
                    return f"""👋 أهلا {name}!

**إزاي أقدر أساعدك؟**
• 💳 رصيدك والأقساط
• ⏰ تذكيرات الدفع
• 🛍️ منتجات مقترحة
• 🧮 احسب قسط جديد
• 🏪 أقرب فرع
• 📱 تغيير البيانات"""
                else:
                    return f"""👋 Hi {name}!

**How can I help?**
• 💳 Balance & installments
• ⏰ Payment reminders
• 🛍️ Product recommendations
• 🧮 Calculate installment
• 🏪 Find branch
• 📱 Update details"""
            else:
                if lang == "ar":
                    return """👋 أهلا بيك في **فُرصة**!

**إزاي أقدر أساعدك؟**
• 📝 فحص التأهل للعضوية
• 📋 الأوراق المطلوبة
• 🧮 حساب القسط الشهري
• 🏪 أقرب فرع للتفعيل"""
                else:
                    return """👋 Welcome to **Forsa**!

**How can I help?**
• 📝 Check eligibility
• 📋 Required documents
• 🧮 Calculate installment
• 🏪 Find nearest branch"""
    
    # ========== FOLLOW-UP HANDLERS ==========
    
    def handle_eligibility_age(self, message, lang, context, user_data):
        age_match = re.search(r'\d+', message)
        if age_match:
            age = int(age_match.group())
            if 21 <= age <= 60:
                context["collected_data"]["age"] = age
                context["awaiting_input"] = "eligibility_salary"
                if lang == "ar":
                    return f"✅ العمر: {age} سنة\n\n**الخطوة 2/3: راتبك كام في الشهر؟**"
                else:
                    return f"✅ Age: {age}\n\n**Step 2/3: What's your monthly salary?**"
            else:
                return "❌ العمر لازم 21-60 سنة. جرب تاني:" if lang == "ar" else "❌ Age must be 21-60. Try again:"
        return "محتاج رقم" if lang == "ar" else "Need a number"
    
    def handle_eligibility_salary(self, message, lang, context, user_data):
        salary_match = re.search(r'\d+', message.replace(',', ''))
        if salary_match:
            salary = int(salary_match.group())
            context["collected_data"]["salary"] = salary
            context["awaiting_input"] = "eligibility_type"
            if lang == "ar":
                return f"✅ الراتب: {salary:,} جنيه\n\n**الخطوة 3/3: موظف ولا صاحب عمل؟**"
            else:
                return f"✅ Salary: {salary:,} EGP\n\n**Step 3/3: Employee or business owner?**"
        return "محتاج رقم" if lang == "ar" else "Need a number"
    
    def handle_eligibility_type(self, message, lang, context, user_data):
        msg_lower = message.lower()
        emp_type = "employee" if any(w in msg_lower for w in ["موظف", "employee"]) else "business" if any(w in msg_lower for w in ["صاحب", "business"]) else None
        
        if emp_type:
            data = context["collected_data"]
            age, salary = data["age"], data["salary"]
            min_salary = 2000 if emp_type == "employee" else 3000
            context["awaiting_input"] = None
            
            if salary >= min_salary:
                limit = min(salary * 10, 100000)
                if lang == "ar":
                    return f"""🎉 **مبروك! أنت مؤهل!**

✅ العمر: {age} | الراتب: {salary:,} جنيه
💳 الحد التقريبي: **{limit:,} جنيه**

**الخطوة الجاية:** زور أقرب فرع مع:
• بطاقة شخصية سارية
• إثبات دخل

**🏪 عايز عنوان الفرع؟**"""
                else:
                    return f"""🎉 **Congratulations! You're eligible!**

✅ Age: {age} | Salary: {salary:,} EGP
💳 Estimated limit: **{limit:,} EGP**

**Next step:** Visit branch with ID & income proof

**🏪 Want branch location?**"""
            else:
                return f"❌ الراتب لازم يكون {min_salary:,} جنيه على الأقل" if lang == "ar" else f"❌ Salary must be at least {min_salary:,} EGP"
        return "اكتب 'موظف' أو 'صاحب عمل'" if lang == "ar" else "Type 'employee' or 'business owner'"
    
    def handle_calculator_amount(self, message, lang, context, user_data):
        amount_match = re.search(r'\d+', message.replace(',', ''))
        if amount_match:
            amount = int(amount_match.group())
            context["collected_data"]["amount"] = amount
            context["awaiting_input"] = "calculator_months"
            if lang == "ar":
                return f"💰 المبلغ: {amount:,} جنيه\n\n**على كام شهر؟** (6، 12، 24)"
            else:
                return f"💰 Amount: {amount:,} EGP\n\n**For how many months?** (6, 12, 24)"
        return "محتاج رقم" if lang == "ar" else "Need a number"
    
    def handle_calculator_months(self, message, lang, context, user_data):
        months_match = re.search(r'\d+', message)
        if months_match:
            months = int(months_match.group())
            amount = context["collected_data"].get("amount", 0)
            context["awaiting_input"] = None
            return calculator.calculate(amount, months, lang)
        return "محتاج رقم" if lang == "ar" else "Need a number"
    
    def handle_phone_change(self, message, lang, context, user_data):
        phone_match = re.search(r'01\d{9}', message.replace(" ", ""))
        if phone_match:
            context["awaiting_input"] = None
            return f"✅ تم تغيير الرقم بنجاح: {phone_match.group()}" if lang == "ar" else f"✅ Phone changed: {phone_match.group()}"
        return "رقم غير صحيح. جرب تاني:" if lang == "ar" else "Invalid number. Try again:"
    
    def handle_email_change(self, message, lang, context, user_data):
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        if email_match:
            context["awaiting_input"] = None
            return f"✅ تم تغيير الإيميل: {email_match.group()}" if lang == "ar" else f"✅ Email changed: {email_match.group()}"
        return "إيميل غير صحيح. جرب تاني:" if lang == "ar" else "Invalid email. Try again:"
    
    def handle_branch_city(self, message, lang, context, user_data):
        # Could expand to handle specific city requests
        pass

ai_engine = ConversationalAI()

# ============ API MODELS ============

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    user_type: Optional[Literal["new", "existing"]] = None

class ChatResponse(BaseModel):
    response: str
    language: str
    session_id: str
    user_type: Optional[str] = None
    intent: Optional[str] = None
    awaiting_input: Optional[str] = None
    ai_enabled: bool

# ============ API ENDPOINTS ============

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    session_id = message.session_id or str(uuid.uuid4())
    session = memory.get_session(session_id)
    
    if message.user_type:
        session["user_type"] = message.user_type
    
    user_data = None
    if session["user_type"] == "existing":
        user_id = message.user_id or "user123"
        user_data = existing_customers.get(user_id, existing_customers["user123"])
        user_data["type"] = "existing"
    elif session["user_type"] == "new":
        user_data = new_customer_template.copy()
        user_data["type"] = "new"
    
    response_text = ai_engine.generate_response(message.message, session, user_data)
    lang = ai_engine.detect_language(message.message)
    intent = ai_engine.detect_intent(message.message)
    
    memory.add_to_history(session_id, "user", message.message, intent)
    memory.add_to_history(session_id, "assistant", response_text)
    
    return ChatResponse(
        response=response_text,
        language=lang,
        session_id=session_id,
        user_type=session["user_type"],
        intent=intent,
        awaiting_input=session["context"].get("awaiting_input"),
        ai_enabled=AI_ENABLED
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "5.4.0-complete",
        "ai_enabled": AI_ENABLED,
        "features": [
            "new_customer_onboarding",
            "existing_customer_support",
            "branch_locator_with_maps",
            "payment_reminders",
            "product_recommendations",
            "smart_calculator",
            "conversation_memory"
        ]
    }


@app.get("/")
async def root():
    return {
        "service": "Forsa Finance AI Chatbot",
        "version": "5.4.0-live",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "health": "/health"
        },
        "message": "Chatbot API is running! Use POST /chat to interact."
    }



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)