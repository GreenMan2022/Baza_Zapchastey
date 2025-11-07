from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os

# --- Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# --- SQLAlchemy ---
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# === Конфигурация ===
app = FastAPI(title="Baza Zapchastey", version="1.0")

# БД (SQLite для простоты, можно заменить на PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zapchasti.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === Модели ===
class Part(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vendor_code = Column(String, unique=True, index=True)
    price = Column(Float, default=0.0)
    source_url = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Создать таблицы
Base.metadata.create_all(bind=engine)

# === Pydantic схемы ===
class PartCreate(BaseModel):
    name: str
    vendor_code: str
    source_url: str

class PartResponse(BaseModel):
    id: int
    name: str
    vendor_code: str
    price: float
    source_url: str
    updated_at: datetime

    class Config:
        from_attributes = True

# === Selenium: Получить драйвер ===
def get_chrome_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument("--single-process")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(15)
    return driver

# === Парсинг цены (пример с любым сайтом) ===
def parse_price(url: str) -> float:
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        time.sleep(3)

        # Пример: ищем по классу или data-атрибуту
        price_selectors = [
            "span.price",
            ".price",
            "[data-price]",
            ".product-price",
            "meta[itemprop='price']"
        ]

        for selector in price_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text or elem.get_attribute("content")
                if text:
                    import re
                    price = re.sub(r"[^\d.,]", "", text).replace(",", ".")
                    return float(price)
            except:
                continue
    except Exception as e:
        print(f"Parse error: {e}")
    finally:
        if driver:
            driver.quit()
    return 0.0

# === API ===
@app.get("/")
def home():
    return {"message": "Baza Zapchastey API работает!", "docs": "/docs"}

@app.post("/parts/", response_model=PartResponse)
def create_part(part: PartCreate):
    db = SessionLocal()
    db_part = Part(
        name=part.name,
        vendor_code=part.vendor_code,
        source_url=part.source_url
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)

    # Асинхронно парсим цену
    try:
        price = parse_price(part.source_url)
        db_part.price = price
        db_part.updated_at = datetime.utcnow()
        db.commit()
    except:
        pass

    db.close()
    return db_part

@app.get("/parts/", response_model=List[PartResponse])
def list_parts():
    db = SessionLocal()
    parts = db.query(Part).all()
    db.close()
    return parts

@app.get("/parse/{vendor_code}")
def parse_single(vendor_code: str):
    db = SessionLocal()
    part = db.query(Part).filter(Part.vendor_code == vendor_code).first()
    if not part:
        raise HTTPException(404, "Запчасть не найдена")
    
    price = parse_price(part.source_url)
    part.price = price
    part.updated_at = datetime.utcnow()
    db.commit()
    db.close()
    return {"vendor_code": vendor_code, "price": price}
