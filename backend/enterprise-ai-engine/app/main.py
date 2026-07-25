import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router
from app.core.security import TokenManager
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main")

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Unified multi-tenant Agentic RAG engine backend serving 4 client portals.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Enterprise AI Engine...")
    
    # Pre-warm connection pool sequentially during boot
    try:
        from app.db.pgvector_client import SupabaseVectorClient
        db_client = SupabaseVectorClient()
        await db_client.connect()
    except Exception as e:
        logger.error(f"Failed to pre-warm database client on startup: {e}")
    
    # Generate helper JWT test tokens for the 4 chatbot channels
    customer_token = TokenManager.generate_token(scope="support", role="guest", user_id="guest_client")
    sales_token = TokenManager.generate_token(scope="sales", role="lead", user_id="lead_client")
    hr_token = TokenManager.generate_token(scope="hr", role="employee", user_id="emp_007")
    it_token = TokenManager.generate_token(scope="it", role="employee", user_id="emp_007")
    
    print("\n" + "=" * 80)
    print("DEVELOPER HELPER: PRE-SIGNED JWT CHANNELS TOKENS FOR LOCAL TESTING")
    print("=" * 80)
    print(f"1. CUSTOMER SUPPORT BOT (scope='support', role='guest'):\nBearer {customer_token}\n")
    print(f"2. SALES BOT (scope='sales', role='lead'):\nBearer {sales_token}\n")
    print(f"3. HR BOT (scope='hr', role='employee'):\nBearer {hr_token}\n")
    print(f"4. IT HELPDESK BOT (scope='it', role='employee'):\nBearer {it_token}\n")
    print("=" * 80 + "\n")

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs": "/docs"
    }
