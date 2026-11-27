import os
import time
import duckdb
from fastapi import FastAPI, HTTPException, Query

# Vercel ke liye writable directory
os.makedirs("/tmp/duckdb_ext", exist_ok=True)

app = FastAPI(title="NumFindr API")

# DuckDB connection setup
con = duckdb.connect(database=":memory:")

# Vercel Fix (Home directory)
con.execute("SET home_directory='/tmp';")
con.execute("SET extension_directory='/tmp/duckdb_ext';")

# httpfs extension load karo (HuggingFace ke liye zaroori)
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# Safe Settings for Vercel
con.execute("SET threads=2;")
con.execute("PRAGMA memory_limit='1GB';")

PARQUET_PATH = "hf://datasets/Bruhletme/Lxfarari/users_data.parquet"

def run_search(search_term: str):
    t0 = time.time()
    clean = search_term.strip()
    
    # Validation (Mobile 10 digit, Aadhar 12 digit)
    if not clean.isdigit() or len(clean) > 12:
        raise HTTPException(status_code=400, detail="Invalid number")
    
    # Mobile ya ID (Aadhar) dono se search
    query = f"""
        SELECT mobile, name, fname, address, alt, circle, id, email
        FROM read_parquet('{PARQUET_PATH}')
        WHERE CAST(mobile AS VARCHAR) = ? OR CAST(id AS VARCHAR) = ?
        LIMIT 1
    """
    
    try:
        rows = con.execute(query, [clean, clean]).fetchall()
        col_names = [desc[0] for desc in con.description] if con.description else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    
    if not rows:
        return {"mobile": clean, "time_sec": round(time.time() - t0, 3), "results": []}
    
    record = dict(zip(col_names, rows[0]))
    return {"mobile": clean, "time_sec": round(time.time() - t0, 3), "results": [record]}

@app.get("/")
def home():
    return {"status": "ok", "source": PARQUET_PATH}

@app.get("/search")
def search_query(q: str = Query(...)):
    return run_search(q)

@app.get("/search/{mobile}")
def search_path(mobile: str):
    return run_search(mobile)
