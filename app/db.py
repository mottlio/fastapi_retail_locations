# app/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import os
from urllib.parse import quote_plus
import dotenv
dotenv.load_dotenv()

# Helper function to read password from secret file or env var
def get_db_password():
    # Try to read from Docker secret file first
    password_file = os.getenv("DB_PASSWORD_FILE")
    if password_file and os.path.exists(password_file):
        with open(password_file, 'r') as f:
            return f.read().strip()
    # Fall back to environment variable
    return os.getenv("DB_PASSWORD")

# Get individual components
db_user = os.getenv("DB_USER", "gasapp")
db_password = get_db_password()
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "gas")

# Build the URL with encoded password
DATABASE_URL = f"postgresql+asyncpg://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"

engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=10)
Session = async_sessionmaker(engine, expire_on_commit=False)

NEARBY_SQL = text("""
SELECT id, name, brand, address, lat, lon,
       ST_Distance(geom, ST_MakePoint(:lon, :lat)::geography)/1000 AS distance_km
FROM gas_stations
WHERE ST_DWithin(geom, ST_MakePoint(:lon, :lat)::geography, :km*1000)
ORDER BY distance_km
LIMIT :limit
""")

async def find_nearby(lat: float, lon: float, km: float = 10, limit: int = 50):
    async with Session() as s:
        rows = (await s.execute(NEARBY_SQL, {"lat": lat, "lon": lon, "km": km, "limit": limit})).mappings().all()
        return [dict(r) for r in rows]
