import httpx
import time
from datetime import datetime, timedelta
import math
import sys

# Constants
LAT = 33.9089
LON = 10.1256
API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def get_target_date_str(days_ago=2):
    target_date = datetime.now() - timedelta(days=days_ago)
    return target_date.strftime("%Y%m%d")

def run_nasa_check():
    # Try dates starting from yesterday going back up to 7 days until we find non -999 data
    found_data = False
    target_date_str = ""
    data = None
    
    print(f"--- NASA POWER API Test for Gabes ({LAT}, {LON}) ---")
    
    for days_ago in range(1, 8):
        temp_date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
        params = {
            "parameters": "T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,WS2M,RH2M",
            "community": "AG",
            "longitude": LON,
            "latitude": LAT,
            "start": temp_date_str,
            "end": temp_date_str,
            "format": "JSON"
        }
        
        try:
            response = httpx.get(API_URL, params=params, timeout=15.0)
            if response.status_code == 200:
                temp_data = response.json()
                # Check if at least one parameter has valid data
                first_param = "T2M_MAX"
                if temp_data["properties"]["parameter"][first_param][temp_date_str] != -999:
                    data = temp_data
                    target_date_str = temp_date_str
                    found_data = True
                    print(f"Target Date: {target_date_str} (found data {days_ago} days ago)\n")
                    break
        except Exception as e:
            print(f"ERROR connecting for date {temp_date_str}: {e}")
            continue

    if not found_data:
        print("ERROR: Could not find any valid data in the last 7 days.")
        print("RESULT: FAILED - do not build agent")
        sys.exit(1)

    warnings = 0
    errors = 0

    # CHECK 1: Connectivity and response time
    # (Already did one request to find date, but let's count it or do another for timing)
    print("CHECK 1 - Connectivity and response time")
    start_time = time.time()
    try:
        response = httpx.get(API_URL, params=params, timeout=15.0)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        print(f"Response time: {elapsed_ms:.0f}ms")
        if elapsed_ms > 5000:
            print("WARNING: Slow response (> 5000ms)")
            warnings += 1
    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        print("\nRESULT: FAILED - do not build agent")
        sys.exit(1)

    # CHECK 2: HTTP status and structure
    print("\nCHECK 2 - HTTP status and structure")
    if response.status_code == 200:
        print("HTTP status: 200 OK")
        try:
            data = response.json()
            if "properties" in data and "parameter" in data["properties"]:
                print("Structure: Valid properties.parameter found")
            else:
                print("ERROR: Response missing 'properties' or 'parameter' keys")
                errors += 1
        except Exception as e:
            print(f"ERROR: Failed to parse JSON: {e}")
            errors += 1
    else:
        print(f"ERROR: HTTP {response.status_code} - {response.text}")
        errors += 1

    if errors > 0:
        print("\nRESULT: FAILED - do not build agent")
        sys.exit(1)

    # CHECK 3: Variable completeness
    print("\nCHECK 3 - Variable completeness")
    variables = ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "WS2M", "RH2M"]
    units = {
        "T2M_MAX": "C",
        "T2M_MIN": "C",
        "ALLSKY_SFC_SW_DWN": "MJ/m2/day",
        "WS2M": "m/s",
        "RH2M": "%"
    }
    ranges = {
        "T2M_MAX": (-50, 60),
        "T2M_MIN": (-50, 60),
        "ALLSKY_SFC_SW_DWN": (0, 40),
        "WS2M": (0, 30),
        "RH2M": (0, 100)
    }
    
    param_data = data["properties"]["parameter"]
    retrieved_vals = {}

    for var in variables:
        if var not in param_data:
            print(f"  {var:<20}: MISSING key [!]")
            warnings += 1
            continue
        
        val_dict = param_data[var]
        val = val_dict.get(target_date_str)
        
        if val == -999 or val is None:
            print(f"  {var:<20}: MISSING (fill value -999) [!]")
            warnings += 1
        else:
            min_r, max_r = ranges[var]
            if not (min_r <= val <= max_r):
                print(f"  {var:<20}: SUSPECT value: {val} [!]")
                warnings += 1
            else:
                print(f"  {var:<20}: {val:>10} {units[var]:<10} [OK]")
                retrieved_vals[var] = val

    # CHECK 4: ET0 sanity calculation
    print("\nCHECK 4 - ET0 sanity calculation")
    can_calc = all(v in retrieved_vals for v in ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN"])
    if can_calc:
        tmax = retrieved_vals["T2M_MAX"]
        tmin = retrieved_vals["T2M_MIN"]
        rs = retrieved_vals["ALLSKY_SFC_SW_DWN"]
        tmean = (tmax + tmin) / 2
        
        et0 = 0.0023 * (tmean + 17.8) * math.sqrt(abs(tmax - tmin)) * rs
        print(f"  ET0 estimate (Hargreaves): {et0:.2f} mm/day")
        
        if not (2 <= et0 <= 10):
            print("  WARNING: ET0 outside expected range (2-10 mm/day)")
            warnings += 1
    else:
        print("  SKIPPED: Missing required variables for ET0 calculation")
        warnings += 1

    # CHECK 5: Latency over 3 consecutive calls
    print("\nCHECK 5 - Latency over 3 consecutive calls")
    latencies = []
    for i in range(3):
        time.sleep(1)
        start_l = time.time()
        try:
            httpx.get(API_URL, params=params, timeout=15.0)
            latencies.append((time.time() - start_l) * 1000)
        except:
            pass
    
    if latencies:
        min_l = min(latencies)
        max_l = max(latencies)
        mean_l = sum(latencies) / len(latencies)
        print(f"  Min: {min_l:.0f}ms, Max: {max_l:.0f}ms, Mean: {mean_l:.0f}ms")
        if mean_l > 3000:
            print("  WARNING: API is slow, consider caching")
            warnings += 1
    else:
        print("  ERROR: Latency check failed (all requests failed)")
        errors += 1

    # Final Summary
    print("\n--- Summary ---")
    if errors > 0:
        print("RESULT: FAILED - do not build agent")
    elif warnings > 0:
        print(f"RESULT: ISSUES FOUND ({warnings} warnings) - review above")
    else:
        print("RESULT: READY")

if __name__ == "__main__":
    run_nasa_check()
