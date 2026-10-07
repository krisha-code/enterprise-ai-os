from app.services.document_text_extractor import DocumentTextExtractor


test_strings = [
    "MODULE 1 – FUNDAMENTALS OF DRONE TECHNOLOGY",
    "1. Fixed-Wing UAV",
    "2. Multi-Rotor UAV",
    "Definition of UAV",
    "Battery level",
    "Target area",
    "Move left",
    "Soil moisture",
    "GROUND CONTROL STATION (GCS)",
]

for text in test_strings:
    result = DocumentTextExtractor.detect_section_title(text)

    print(f"{text!r} -> {result!r}")