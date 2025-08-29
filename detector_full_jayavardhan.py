import pandas as pd
import re
import sys
import random

AADHAAR_PATTERN = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
PHONE_PATTERN = re.compile(r'\b\d{10}\b')
PASSPORT_PATTERN = re.compile(r'\b[A-Z][0-9]{7}\b')
UPI_PATTERN = re.compile(r'\b[\w\d._%+-]+@[\w\d.-]+\b')

def redact_standalone(key, value):
    value = str(value)
    if key == "phone":
        return value[:2] + "XXXXXX" + value[-2:]
    elif key == "aadhaar":
        return value[:4] + " XXXX XXXX"
    elif key == "passport":
        return value[0] + "XXXXXXX"
    elif key == "upi_id":
        parts = value.split('@')
        return parts[0][:2] + "XXXX" + "@" + parts[1]
    return value

def humanize_redaction(key, value):
    value = str(value)
    if key == "name":
        parts = value.split()
        if len(parts) >= 2:
            return parts[0][0] + "".join(random.choices("X", k=random.randint(2,4))) + " " + parts[-1][0] + "".join(random.choices("X", k=random.randint(2,4)))
        return "X XXX"
    elif key == "email":
        local, domain = value.split("@")
        return local[0] + "".join(random.choices("X", k=random.randint(2,4))) + "@" + domain
    elif key == "address":
        return re.sub(r'\d+', lambda x: "XX", value)
    elif key in ["ip_address", "device_id"]:
        return re.sub(r'\d+$', lambda x: "XXX", value)
    return value

def detect_and_redact(record):
    pii_found = False
    redacted = record.copy()
    for key in ['phone', 'aadhar', 'passport', 'upi_id']:
        value = redacted.get(key)
        if value:
            if key == 'phone' and PHONE_PATTERN.fullmatch(str(value)):
                redacted[key] = redact_standalone("phone", value)
                pii_found = True
            elif key == 'aadhar' and AADHAAR_PATTERN.fullmatch(str(value)):
                redacted[key] = redact_standalone("aadhaar", value)
                pii_found = True
            elif key == 'passport' and PASSPORT_PATTERN.fullmatch(str(value)):
                redacted[key] = redact_standalone("passport", value)
                pii_found = True
            elif key == 'upi_id' and UPI_PATTERN.fullmatch(str(value)):
                redacted[key] = redact_standalone("upi_id", value)
                pii_found = True
    combinatorial_keys = ['name', 'email', 'address', 'device_id', 'ip_address']
    detected_combinatorial = []
    for key in combinatorial_keys:
        value = redacted.get(key)
        if value:
            detected_combinatorial.append(key)
            redacted[key] = humanize_redaction(key, value)
    if len(detected_combinatorial) >= 2:
        pii_found = True
    return redacted, pii_found

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 detector_full_jayavardhan.py input.csv")
        sys.exit(1)
    input_csv = sys.argv[1]
    df = pd.read_csv(input_csv)
    df.rename(columns=lambda x: x.strip().replace(" ", "_").lower(), inplace=True)
    if 'record_id' not in df.columns or 'data_json' not in df.columns:
        print("CSV must contain 'record_id' and 'data_json' columns.")
        sys.exit(1)
    output_rows = []
    for _, row in df.iterrows():
        record_id = row['record_id']
        try:
            data_json = eval(row['data_json'])
        except:
            continue
        redacted_json, is_pii = detect_and_redact(data_json)
        output_rows.append({
            'record_id': record_id,
            'redacted_data_json': str(redacted_json),
            'is_pii': is_pii
        })
    output_df = pd.DataFrame(output_rows)
    output_csv = "redacted_output_jayavardhan.csv"
    output_df.to_csv(output_csv, index=False)
    print(f"Redacted CSV generated: {output_csv}")

if __name__ == "__main__":
    main()
