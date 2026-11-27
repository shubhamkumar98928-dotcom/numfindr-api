import os
import time
import duckdb
from fastapi import FastAPI, HTTPException, Query

# Vercel ke liye writable directory
os.makedirs("/tmp/duckdb_ext", exist_ok=True)

app = FastAPI(title="NumFindr API")

# DuckDB connection setup
con = duckdb.connect(database=":memory:")

# Vercel fix
con.execute("SET home_directory='/tmp';")
con.execute("SET extension_directory='/tmp/duckdb_ext';")

# httpfs extension load karo
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# 🚀 SPEED SETTINGS (Naya Code)
con.execute("SET threads=4;")             # 4 threads use karega
con.execute("PRAGMA memory_limit='2GB';") # 2GB memory de rahe hain
con.execute("SET http_timeout=120000;")   # Network timeout 120 sec kar diya

PARQUET_PATH = "hf://datasets/Bruhletme/Lxfarari/users_data.parquet"

def run_search(search_term: str):
    t0 = time.time()
    clean = search_term.strip()
    
    if not clean.isdigit() or len(clean) > 12: # Aadhar ke liye 12 digits tak allow kiya
        raise HTTPException(status_code=400, detail="Invalid number")
    
    # 🚀 Dono mobile aur id (Aadhar) se search karne ke liye query update ki
    query = f"""
        SELECT mobile, name, fname, address, alt, circle, id, email
        FROM read_parquet('{PARQUET_PATH}')
        WHERE CAST(mobile AS VARCHAR) = ? OR CAST(id AS VARCHAR) = ?
        LIMIT 1
    """
    
    try:
        # Dono jagah same number pass kar rahe hain
        rows = con.execute(query, [clean, clean]).fetchall()
        col_names = [desc[0] for desc in con.description] if con.description else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    
    if not rows:
        return {
            "mobile": clean,
            "time_sec": round(time.time() - t0, 3),
            "results": []
        }
    
    record = dict(zip(col_names, rows[0]))
    return {
        "mobile": clean,
        "time_sec": round(time.time() - t0, 3),
        "results": [record]
    }

@app.get("/")
def home():
    return {
        "status": "ok",
        "source": PARQUET_PATH,
        "note": "DuckDB querying directly from Hugging Face"
    }

@app.get("/search")
def search_query(q: str = Query(..., description="Mobile or Aadhar number")):
    return run_search(q)

@app.get("/search/{mobile}")
def search_path(mobile: str):
    return run_search(mobile)
