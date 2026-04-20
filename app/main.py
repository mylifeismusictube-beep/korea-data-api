"""
Korea Data API - Public Korean data in English
For RapidAPI marketplace distribution.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.holidays import HOLIDAYS

app = FastAPI(
    title="Korea Data API",
    description="Public Korean data (holidays, subway, stocks) in English. Built for developers worldwide.",
    version="1.0.0",
    contact={"name": "Korea Data API", "url": "https://rapidapi.com/"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "Korea Data API",
        "version": "1.0.0",
        "endpoints": {
            "/holidays/year/{year}": "Get all Korean public holidays for a year (2020-2030)",
            "/holidays/year/{year}/month/{month}": "Get holidays for a specific month",
            "/holidays/check/{date}": "Check if a specific date is a Korean holiday",
            "/holidays/next": "Get the next upcoming Korean holiday",
            "/holidays/range": "Get holidays within a date range",
        },
        "supported_years": "2020-2030",
    }


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "years_loaded": list(HOLIDAYS.keys())}


@app.get(
    "/holidays/next",
    operation_id="getNextHoliday",
    summary="Get Next Holiday",
    description="Returns the next upcoming Korean public holiday from today or a given date.",
    tags=["Holidays"],
)
def next_holiday(from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD. Defaults to today.")):
    """Get the next upcoming Korean public holiday."""
    if from_date:
        try:
            base = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD")
    else:
        base = date.today()

    for year in range(base.year, 2031):
        if year not in HOLIDAYS:
            continue
        for h in HOLIDAYS[year]:
            hd = datetime.strptime(h["date"], "%Y-%m-%d").date()
            if hd >= base:
                return {
                    "from_date": str(base),
                    "days_until": (hd - base).days,
                    "holiday": h,
                }
    raise HTTPException(status_code=404, detail="No upcoming holidays in dataset")


@app.get(
    "/holidays/range",
    operation_id="getHolidaysInRange",
    summary="Get Holidays In Date Range",
    description="Returns all Korean public holidays that fall between two dates (inclusive).",
    tags=["Holidays"],
)
def holidays_in_range(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
):
    """Get all Korean public holidays within a date range."""
    try:
        s = datetime.strptime(start, "%Y-%m-%d").date()
        e = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD")

    if s > e:
        raise HTTPException(status_code=400, detail="start must be <= end")

    result = []
    for year in range(s.year, e.year + 1):
        if year not in HOLIDAYS:
            continue
        for h in HOLIDAYS[year]:
            hd = datetime.strptime(h["date"], "%Y-%m-%d").date()
            if s <= hd <= e:
                result.append(h)
    return {
        "start": start,
        "end": end,
        "count": len(result),
        "holidays": result,
    }


@app.get(
    "/holidays/check/{check_date}",
    operation_id="checkIfDateIsHoliday",
    summary="Check If Date Is Holiday",
    description="Check whether a specific date is a Korean public holiday. Also returns day of week and weekend status.",
    tags=["Holidays"],
)
def check_holiday(check_date: str):
    """Check if a specific date (YYYY-MM-DD) is a Korean public holiday."""
    try:
        d = datetime.strptime(check_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD")

    year = d.year
    if year not in HOLIDAYS:
        raise HTTPException(status_code=404, detail=f"Year {year} not supported")

    match = next((h for h in HOLIDAYS[year] if h["date"] == check_date), None)
    return {
        "date": check_date,
        "is_holiday": match is not None,
        "holiday": match,
        "is_weekend": d.weekday() >= 5,
        "day_of_week": d.strftime("%A"),
    }


@app.get(
    "/holidays/year/{year}",
    operation_id="getHolidaysByYear",
    summary="Get Holidays By Year",
    description="Returns all Korean public holidays for a given year (2020-2030). Includes fixed, lunar, substitute, and temporary holidays.",
    tags=["Holidays"],
)
def get_holidays_by_year(
    year: int,
    type: Optional[str] = Query(None, description="Filter by type: fixed, lunar, substitute, temporary"),
):
    """Get all Korean public holidays for a given year."""
    if year not in HOLIDAYS:
        raise HTTPException(
            status_code=404,
            detail=f"Year {year} not supported. Available: 2020-2030",
        )
    holidays = HOLIDAYS[year]
    if type:
        holidays = [h for h in holidays if h["type"] == type]
    return {
        "year": year,
        "count": len(holidays),
        "holidays": holidays,
    }


@app.get(
    "/holidays/year/{year}/month/{month}",
    operation_id="getHolidaysByMonth",
    summary="Get Holidays By Month",
    description="Returns Korean public holidays for a specific month of a given year.",
    tags=["Holidays"],
)
def get_holidays_by_month(year: int, month: int):
    """Get Korean public holidays for a specific month."""
    if year not in HOLIDAYS:
        raise HTTPException(status_code=404, detail=f"Year {year} not supported")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be 1-12")

    month_str = f"{year}-{month:02d}"
    holidays = [h for h in HOLIDAYS[year] if h["date"].startswith(month_str)]
    return {
        "year": year,
        "month": month,
        "count": len(holidays),
        "holidays": holidays,
    }
