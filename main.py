from fastapi import FastAPI, HTTPException, Query
import duckdb
import time

app = FastAPI(title="NumFindr API")

# DuckDB memory connection
con = duckdb.connect(database=":memory:")
con.execute("PRAGMA threads=2;")
con.execute("PRAGMA memory_limit='1GB';")  # Vercel free tier ke liye kam

# Hugging Face path — file locally nahi chahiye
PARQUET_PATH = "hf://datasets/Bruhletme/Lxfarari/users_data.parquet"

def run_search(mobile: str):
    t0 = time.time()
    clean = mobile.strip()
    
    if not clean.isdigit() or len(clean) > 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number")
    
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
        return {"mobile": clean, "time_sec": round(time.time() - t0, 3), "results": []}
    
    record = dict(zip(col_names, rows[0]))
    return {"mobile": clean, "time_sec": round(time.time() - t0, 3), "results": [record]}

@app.get("/")
def home():
    return {"status": "ok", "source": PARQUET_PATH}

@app.get("/search")
def search_query(mobile: str = Query(...)):
    return run_search(mobile)

@app.get("/search/{mobile}")
def search_path(mobile: str):
    return run_search(mobile)