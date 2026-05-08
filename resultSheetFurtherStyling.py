import json
import re
import math
import base64
import os
import logging
from datetime import datetime, date
import sys


# Configure logging
logging.basicConfig(
    filename="transform.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
if len(sys.argv) >1:
    print(f"there is {len(sys.argv)-1} input argument")
else:
    print(f"there is no input argument")

INPUT_FILE = next(
        (arg for arg in reversed(sys.argv) if "_resultSheetJson_" in arg),
        "_default_:C:/Users/Iqtidar3.14/allProject/assets/admissionForm/admissionFormData/valid_rolls_missingAdmissionRoll_20250910_175731.json"
    )


print(f"using {INPUT_FILE} as resultSheetJson")
INPUT_FILE = str(INPUT_FILE.split("_:")[1])
REFERENCE_DATE = None
if REFERENCE_DATE is None:
    REFERENCE_DATE = datetime.today().date()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_foldaer = "./assets/resultScraping/cleanedResultSheet"
os.makedirs(output_foldaer, exist_ok=True)
OUTPUT_FILE = f"{output_foldaer}/cleaned_{timestamp}.json"

# ---------------- Helper Functions ---------------- #













def transform_record(record):
    r = record.copy()

    # Clean up fields

    status = str(r.get("status"))
    

    # clean academicYear → keep only digits
    if "academicYear" in r:
        r["academicYear"] = re.sub(r'[^0-9]', '', r["academicYear"])

    fields = ["cq", "mcq", "practical", "termTotal", "grade", "gp"]
    new_record = {}
    for subject, scores in r.items():
        if isinstance(scores, dict):
            # ✅ Only remove if ALL fields are present and empty
            if all(field in scores for field in fields) and all(scores[field] == "" for field in fields):
                continue  # skip this subject
        new_record[subject] = scores
    r = new_record
    for subject, scores in r.items():
        if isinstance(scores, dict):
            # Replace cq if empty or blank or A
            if "cq" in scores:
                if scores["cq"].strip() == "" or scores["cq"] == "A":
                    scores["cq"] = "A"

    # r is a single student record
    subject_count = 0
    for subject, scores in r.items():
        if isinstance(scores, dict):
            # count only if it has all six keys
            if all(field in scores for field in fields):
                subject_count += 1
    # add the count to the record
    if status == "qualified":
        r["subjectCount"] = subject_count

    perSubjectTotalNumber = 20
    totalWithAdditional = r.get("totalWithAdditional", 0)
    try:
        totalWithAdditional = float(totalWithAdditional)
    except ValueError:
        totalWithAdditional = 0  # fallback if conversion fails
    if subject_count > 0 and totalWithAdditional>0:
        avgNumber = round(totalWithAdditional / subject_count, 2)
        if status == "qualified":
            r["avgNumber"] = str(avgNumber)
    elif subject_count == 0:
        avgNumber = 0
    else:
        avgNumber = 0
        if status == "qualified":
            r["avgNumber"] = str(avgNumber)
    
    avgNumberPerCent = round(avgNumber * 100/perSubjectTotalNumber, 2)
    if status == "qualified":
        r["avgNumberPerCent"] = str(avgNumberPerCent)
    
    class_roll = r.get("classRoll", "")
    if len(class_roll) >= 9:
        group_digit = class_roll[8]
        if group_digit == "1":
            r["group3"] = "Sci"
        elif group_digit == "2":
            r["group3"] = "Bus"
        elif group_digit == "3":
            r["group3"] = "Hum"
        else:
            r["group3"] = ""
    else:
        r["group3"] = ""

    # Section
    if r["group3"] == "Sci":
        try:
            last3 = int(class_roll[-3:])
            idx = math.ceil(last3 / 150) if last3 > 0 else 1
            mapping = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
            r["Section"] = mapping.get(idx, "")
        except:
            r["Section"] = ""
    else:
        r["Section"] = ""

    # Batch
    try:
        segment = int(class_roll[5:7])
        r["Batch"] = str(segment + 1)
    except:
        r["Batch"] = ""


    r["roll"] = str(r["classRoll"])[-3:]
    r["name"] = r.get("studentName")
    if status == "qualified" and totalWithAdditional == 0:
        status = "absent"
        r["status"] = str(status)
    r["status"] = r.pop("status")

    if status == "qualified":
        r["gpa"] = float(r.get("gpaWithAdditional"))
        r["totalMark"] = totalWithAdditional
        r["avgMark(%)"] = avgNumberPerCent 

    return r
def ranking(cleaned):
    data = cleaned.copy()

    # Convert numeric fields for proper sorting (only for qualified students)
    qualified_students = []
    for student in data:
        student["roll"] = int(student.get("roll", 0))
        if student.get("status") == "qualified":
            student["gpaWithAdditional"] = float(student.get("gpaWithAdditional", 0))
            student["gpaWithoutAdditional"] = float(student.get("gpaWithoutAdditional", 0))
            student["avgNumberPerCent"] = float(student.get("avgNumberPerCent", 0))
            student["totalWithAdditional"] = int(student.get("totalWithAdditional", 0))
            qualified_students.append(student)

    # ---- WHOLE RANKING (all qualified students) ----
    ranking_sorted = sorted(
        qualified_students,
        key=lambda x: (
            -x["gpaWithAdditional"],
            -x["gpaWithoutAdditional"],
            -x["avgNumberPerCent"],
            -x["totalWithAdditional"],
            x["roll"]
        )
    )
    overall_rankings = {s["roll"]: idx + 1 for idx, s in enumerate(ranking_sorted)}
    # ---- SECTION RANKING ----
    sections = {
        "A": range(1, 151),
        "B": range(151, 301),
        "C": range(301, 451),
        "D": range(451, 601),
        "E": range(601, 751),
        "F": range(751, 901),
    }
    
    section_rankings = {}
    
    for sec, roll_range in sections.items():
        # filter ONLY Science students belonging to this section
        sec_students = [
            s for s in qualified_students
            if s["roll"] in roll_range and s.get("group3") == "Sci"
        ]
        # sort them by same criteria
        sorted_sec = sorted(
            sec_students,
            key=lambda x: (
                -x["gpaWithAdditional"],
                -x["gpaWithoutAdditional"],
                -x["avgNumberPerCent"],
                -x["totalWithAdditional"],
                x["roll"]
            )
        )
        # assign section ranks
        for idx, s in enumerate(sorted_sec, start=1):
            section_rankings[s["roll"]] = idx
    
    # ---- ADD RANKINGS BACK TO ALL STUDENTS ----
    for student in cleaned:
        if student.get("status") == "qualified":
            student["Ranking"] = {
                "global": overall_rankings[student["roll"]],
                "section": section_rankings.get(student["roll"], None)  # None if not Sci
            }


    # ---- FINAL SORT BY roll ----
    cleaned.sort(key=lambda x: x["roll"])
    for student in cleaned: 
        student["roll"] = student.get("roll")
    print("JSON sorted by roll with global and section rankings added for qualified students!")
    return cleaned



# ---------------- Main ---------------- #

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned = [transform_record(rec) for rec in data]
ranked_data = ranking(cleaned)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(ranked_data, f, ensure_ascii=False, indent=2)

logging.info(f"Transformation complete. Processed {len(cleaned)} records.")
print(f"saved as {OUTPUT_FILE}")

with open("./scripts/collegePdf/resultScraping/workflowResultSheet.txt", "a") as f:
    f.write( "\n" + f"_cleanResultSheet_{timestamp}_:" + os.path.abspath(OUTPUT_FILE))

