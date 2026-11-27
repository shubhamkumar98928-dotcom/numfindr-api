import os
import time
import duckdb
from fastapi import FastAPI, HTTPException, Query

# Vercel mein writable directory sirf /tmp hoti hai
os.makedirs("/tmp/duckdb_ext", exist_ok=True)

app = FastAPI(title="NumFindr API")

# DuckDB connection setup
con = duckdb.connect(database=":memory:")

# 🛠️ Vercel Fixes
con.execute("SET home_directory='/tmp';")
con.execute("SET extension_directory='/tmp/duckdb_ext';")

# httpfs extension load karo (HuggingFace ke liye zaroori)
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# 🚀 Speed Settings (Thoda fast karne ke liye)
con.execute("PRAGMA threads=8;")             # 4 se badha kar 8 kiya
con.execute("PRAGMA memory_limit='2GB';")    # 1GB se badha kar 2GB kiya

PARQUET_PATH = "hf://datasets/Bruhletme/Lxfarari/users_data.parquet"

def run_search(mobile: str):
    t0 = time.time()
    clean = mobile.strip()
    
    if not clean.isdigit() or len(clean) > 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number")
    
    # Sirf mobile se search (jo pehle chal raha tha)
    query = f"""
        SELECT mobile, name, fname, address, alt, circle, id, email
        FROM read_parquet('{PARQUET_PATH}')
        WHERE CAST(mobile AS VARCHAR) = ?
        LIMIT 1
    """
    
    try:
        rows = con.execute(query, [clean]).fetchall()
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
def search_query(mobile: str = Query(..., description="10 digit mobile number")):
    return run_search(mobile)

@app.get("/search/{mobile}")
def search_path(mobile: str):
    return run_search(mobile)
