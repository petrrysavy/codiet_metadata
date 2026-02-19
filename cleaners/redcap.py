from settings import *
import pandas as pd
from checkers import test_data_frame
from preprocess import *
from metadata import DataFrameMetadata
from inputoutput import save
import re

RAW_FILE_NAME = f"REDcap_data_combined_nov2024.xlsx"

df = pd.read_excel(os.path.join(Settings().getdir(SettingsKeys.RAWDIR), RAW_FILE_NAME), header=0, sheet_name="datos todos")
print(df)
print(df.columns)
print(df.shape)

pd.set_option('display.max_rows', 200)
column_comments = {}
column_units = {}

df = df.rename(columns={"volunteer_id": "patient", "recruitment_site": "site", "Sex": "gender"})
df = clean_patient_column(df)
df = clean_site_column(df)

#### ETHNICITY
def split_ethnicity(x):
    # Handle special case
    if x.lower().startswith("not informed"):
        return pd.Series([np.nan, np.nan])

    # Normalize separators
    x = x.replace(" - ", "-").replace("–", "-")

    parts = x.split("-", 1)
    if len(parts) == 1:
        # No dash present -> treat whole as broad group
        return pd.Series([parts[0], np.nan])
    else:
        return pd.Series(parts)

df[['ethnicity', "ethnicity-subcategory"]] = df['Ethnicity'].apply(split_ethnicity)
df = df.drop(columns=['Ethnicity'])

print(df[['ethnicity', "ethnicity-subcategory"]])

df["Living Status"] = df["Living Status"].str.removeprefix("Living ")

# PROFESSION
df = df.rename(columns={"If you answered working, please fill in: current profession and years working": "profession"})
print(df.shape)

def parse_profession_and_years(text):
    if pd.isna(text):
        return pd.Series([np.nan, np.nan])

    s = text.strip()
    # Normalize decimals that use commas
    s = s.replace(",", ".")
    # LOWERCASE version just for regex matching
    sl = s.lower()
    # Extract years/months first
    years = np.nan
    # Pattern examples:
    # "20 years", "20y", "6 months", "1.5 years", "9 months", "for 40 years"
    match = re.search(r'(\d+(\.\d+)?)\s*(year|years|y)', sl)
    if match:
        years = float(match.group(1))
    else:
        # Try months
        match = re.search(r'(\d+(\.\d+)?)\s*(month|months|m)', sl)
        if match:
            years = float(match.group(1)) / 12
        else: # search just for numbers
            match = re.search(r'(\d+)\s*$', sl)
            if match:
                years = float(match.group(1))

    # Remove trailing duration part from the profession text
    cleaned = re.sub(r',?\s*(for)?\s*\d+(\.\d+)?\s*(year|years|y|month|months|m)?\w*', '', sl, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r',?\s*(\d+)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
    # Title case for nicer output
    cleaned = cleaned.title()
    return pd.Series([cleaned, years])

# Apply to DataFrame
df[["profession", "years-working"]] = df["profession"].apply(parse_profession_and_years)
df["profession"] = df["profession"].str.removesuffix(".")
print(df[["profession", "years-working"]])

df = df.rename(columns={"If you answered not working, please fill last profession and years working": "last-profession"})
df[["last-profession", "last-years-working"]] = df["last-profession"].apply(parse_profession_and_years)
print(df[["last-profession", "last-years-working"]])

df["profession"] = df["profession"].fillna(df["last-profession"])
df["years-working"] = df["years-working"].fillna(df["last-years-working"])
df = df.drop(columns=["last-profession", "last-years-working"])

df = df.rename(columns={"If you answered retired, please fill in, last profession and years working": "retired-profession"})
df[["retired-profession", "retired-years-working"]] = df["retired-profession"].apply(parse_profession_and_years)
df["profession"] = df["profession"].fillna(df["retired-profession"])
df["years-working"] = df["years-working"].fillna(df["retired-years-working"])
df = df.drop(columns=["retired-profession", "retired-years-working"])

df["profession"] = df["profession"].str.removesuffix(".")
print(df)
print(df[["profession", "years-working"]].iloc[19:,])

column_comments["profession"] = "Current profession if working, last profession otherwise."
column_comments["years-working"] = "Years spent working, answered together with profession."
column_units["years-working"] = "years"

## SALARY
df = df.rename(columns = {"Salary (annual net salary)": "salary"})
column_comments["salary"] = ("Annual net salary.")

df = df.rename(columns = {"If you answered shift worker, please describe your shifts patterns": "shift-patterns"})
df.loc[df["Working time"] != "Shift worker", "shift-patterns"] = pd.NA

## Womans HEALTH
df = df.rename(columns = {"Women's health (only for women)  Please fill in the following information:  Years of menarche  Years of menopause  Number of children  Number of full-term pregnancies  Currently breastfeeding?  Did you breastfeed your children? If yes, how many?": "womens-health"})
df.loc[df["gender"] != "Female", "womens-health"] = pd.NA


def parse_women_health(text):
    if pd.isna(text) or str(text).strip() == "":
        return pd.Series([np.nan] * 6)

    s = str(text).lower()
    s = s.replace("–", "-").replace("—", "-").replace("’", "'")

    # Initialize defaults
    menarche = menopause = children = pregnancies = np.nan
    curr_bf = ever_bf = np.nan

    # --- normalize separators ---
    s = s.replace(";", ",").replace("|", ",")

    # --- explicit key/value patterns ---
    menarche_match = re.search(r"menarche[^0-9]*(\d+\.?\d*)", s)
    menopause_match = re.search(r"menopause[^0-9]*(\d+\.?\d*)", s)
    children_match = re.search(r"children[^0-9]*(\d+)", s)
    preg_match = re.search(r"pregnanc(?:y|ies)[^0-9]*(\d+)", s)
    curr_bf_match = re.search(r"(currently breastfeeding|breastfeeding[^a-z]*:?)\s*(yes|no|y|n)", s)
    ever_bf_match = re.search(r"(breastfeed[^a-z]*(child|children)?)[^a-z]*(yes|no|y|n)", s)

    # --- simple comma-separated numeric cases ---
    nums = [n.strip() for n in re.split(r"[,/]", s) if re.search(r"\d", n)]

    # Assign numbers heuristically if not already matched
    if menarche_match:
        menarche = float(menarche_match.group(1))
    elif len(nums) > 0:
        menarche = float(re.findall(r"\d+\.?\d*", nums[0])[0])

    if menopause_match:
        menopause = float(menopause_match.group(1))
    elif len(nums) > 1:
        val = re.findall(r"\d+\.?\d*", nums[1])
        if val:
            menopause = float(val[0])

    if children_match:
        children = float(children_match.group(1))
    elif len(nums) > 2:
        children = float(re.findall(r"\d+\.?\d*", nums[2])[0])

    if preg_match:
        pregnancies = float(preg_match.group(1))
    elif len(nums) > 3:
        pregnancies = float(re.findall(r"\d+\.?\d*", nums[3])[0])

    # breastfeeding yes/no flags
    if curr_bf_match:
        curr_bf = True if "y" in curr_bf_match.group(2) else False
    elif re.search(r"\bcurrently breastfeeding\b.*yes", s):
        curr_bf = True
    elif re.search(r"\bcurrently breastfeeding\b.*no", s):
        curr_bf = False

    if ever_bf_match:
        ever_bf = True if "y" in ever_bf_match.group(3) else False

    return pd.Series([menarche, menopause, children, pregnancies, curr_bf, ever_bf])

df[["menarche-years", "menopause-years", "n-children", "n-pregnancies", "currently-breastfeeding", "ever-breastfed"]] = df["womens-health"].apply(parse_women_health)
df = df.convert_dtypes()  # sets pd.NA instead of np.nan

print(df[["menarche-years", "menopause-years", "n-children", "n-pregnancies", "currently-breastfeeding", "ever-breastfed"]])
df = df.drop(columns="womens-health")


## SMOKING

df = df.rename(columns = {"If you answered former smoker, please fill in the following details:  Number of cigarettes per day  Years smoking  Years without smoking  Age started smoking": "smokers"})
df.loc[df["Smoking status"] != "Former smoker", "smokers"] = pd.NA


def parse_smoking_info(entry, exp=4):
    if pd.isna(entry) or str(entry).strip() == "":
        return pd.Series([pd.NA] * exp)

    # Standardize
    entry = entry.replace("started at 13 years old", ",,,13").replace("10,18.7,18 years old,","10,18,7,18").replace("40/d, 25y, 15yo","40,25,12,15")
    entry = (entry.lower().replace("cigarettes smoked per day", "").replace("cigarettes", "").replace("2 packs", "40")
             .replace("3packs/day", "60").replace("2pack/day", "40").replace("pack", "20").replace("/day", ""))
    entry = entry.replace("per day", "").replace("years old","").replace("years", "").replace("yo", "").replace("y", "").replace(
        "started at", "").replace("of smoking", "").replace("without smoking", "").replace("smoking", "")
    entry = entry.replace("?.3", "?,3").replace("/d", "").replace("?. 15", "?,15").replace("4months", "0.33")

    # Split by common separators
    parts = re.split(r'[,;/]', entry)
    if len(parts) != exp: print("!!!!!!!!!!!!!!")
    print(parts)

    numbers = []
    for p in parts:
        # Extract numbers, average ranges if needed
        nums = re.findall(r'\d+\.?\d*', p)
        if nums:
            if '-' in p:  # handle ranges
                n1, n2 = map(float, re.findall(r'\d+\.?\d*', p))
                numbers.append((n1 + n2) / 2)
            else:
                numbers.append(float(nums[0]))
        else:
            numbers.append(pd.NA)

    # Ensure length 4
    while len(numbers) < exp:
        numbers.append(pd.NA)

    return pd.Series(numbers[:exp])

df[["cigaretes-per-day", "years-smoking", "years-withnout-smoking", "age-started-smoking"]] = df["smokers"].apply(parse_smoking_info)
df = df.drop(columns="smokers")
print(df[["cigaretes-per-day", "years-smoking", "years-withnout-smoking", "age-started-smoking"]])

parse_smoking_info_three = lambda x: parse_smoking_info(x, 3)

df = df.rename(columns={"If you answered current smoker, please fill in the following details:  number of cigarettes smoked per day  years smoking  age started smoking": "smokers"})
df.loc[df["Smoking status"] != "Current smoker", "smokers"] = pd.NA
df[["cigaretes-per-day-curr", "years-smoking-curr", "age-started-smoking-curr"]] = df["smokers"].apply(parse_smoking_info_three)
df = df.drop(columns="smokers")
print(df[["cigaretes-per-day-curr", "years-smoking-curr", "age-started-smoking-curr"]])

df["cigaretes-per-day"] = df["cigaretes-per-day"].fillna(df["cigaretes-per-day-curr"])
df["years-smoking"] = df["years-smoking"].fillna(df["years-smoking-curr"])
df["age-started-smoking"] = df["age-started-smoking"].fillna(df["age-started-smoking-curr"])
df = df.drop(columns=["cigaretes-per-day-curr", "years-smoking-curr", "age-started-smoking-curr"])

column_comments["cigaretes-per-day"] = column_comments["years-smoking"] = column_comments["age-started-smoking"] = "Details applicable to current and former smokers."

### DIET
df = df.rename(columns={"Are you following a specific diet?": "diet",  "If you filled in other for diet, please describe your diet": "diet-description"})
df.replace("Other (please specify below)", "Other", inplace=True)
df.loc[df['diet-description'].isin(["Not on any specific diet", "0", "No"]), 'diet'] = "no diet"
df.loc[df['diet-description'].isin(["Not on any specific diet", "0", "No"]), 'diet-description'] = pd.NA


df.replace("Other (please specify in the next question)", "Other", inplace=True)
df = df.rename(columns={"Medical history. Did you have any of the following conditions?": "medical-history",
               "If you answered other in the above question please describe here your medical history": "medical-history-other"})
df["medical-history-other"] = df["medical-history-other"].replace("0", pd.NA)

print(df[["diet", "diet-description", "medical-history", "medical-history-other"]])


### SLEEP
df = df.rename(columns={"How many hours per day do you sleep during workdays?": "sleep-workdays",
                        "How many hours per day do you sleep during free days?": "sleep-free-days"})
column_units["sleep-workdays"] = "hours"
column_units["sleep-free-days"] = "hours"

def parse_sleep_time(value):
    if pd.isna(value):
        return pd.NA
    s = str(value).strip().lower()
    # Replace comma with dot
    s = s.replace(",", ".")
    # Handle Excel date-like (assume it's just the day part)
    if re.match(r'\d{2}-[a-z]{3}', s):
        s = s[:2]  # take day number
        try:
            return float(s) + 0.5
        except:
            return pd.NA

    # Handle "6h 30 min" or "5 h 30 min"
    match = re.match(r'(\d+(?:\.\d+)?)\s*h\s*(\d+)\s*min', s)
    if match:
        hours = float(match.group(1)) + float(match.group(2)) / 60
        return hours
    # Handle ranges "6-7" to average
    if "-" in s:
        parts = s.split("-")
        try:
            nums = [float(p) for p in parts]
            return sum(nums) / len(nums)
        except:
            return pd.NA
    # Handle plain numbers
    try:
        return float(s)
    except:
        return pd.NA

df['sleep-workdays'] = df['sleep-workdays'].apply(parse_sleep_time)
df['sleep-free-days'] = df['sleep-free-days'].apply(parse_sleep_time)
print(df[["sleep-workdays", "sleep-free-days"]])

#### NAPS
df = df.rename(columns={"Do you take naps during the day?": "naps-during-day",
                        "If you answered yes in the above question, please mention how many naps and how long they are.": "naps-descr"})
df.loc[df["naps-during-day"] != "Yes", "naps-descr"] = pd.NA
df['naps-during-day'] = df['naps-during-day'].map({'Yes': True, 'No': False}).astype('boolean')



#### SLEEP and activity
df = df.rename(columns={"Rate your sleep quality (1: very bad, 5: very good)": "sleep-quality"})
activity_set = {
    "We are interested in finding out about the kinds of physical activities that people do as part of their everyday lives.  The questions will ask you about the time you spent being physically active in the last 7 days. Please answer each question even if yo": "days-active",
    "How much time did you usually spend doing vigorous physical activities on one of those days? Please answer in hours and minutes per day.": "vigorous-time",
    "Think about all the moderate activities that you did in the last 7 days. Moderate activities refer to activities that take moderate physical effort and make you breathe somewhat harder than normal. Think only about those physical activities that you did f": "days-moderate-activity",
    "How much time did you usually spend doing moderate physical activities on one of those days? Please answer in hours and minutes": "moderate-time",
    "Think about the time you spent walking in the last 7 days. This includes at work and at home, walking to travel from place to place, and any other walking that you have done solely for recreation, sport, exercise, or leisure.    During the last 7 days, on": "days-walking-activity",
    "How much time did you usually spend walking on one of those days? Please answer in hours and minutes.": "walking-time",
    "The last question is about the time you spent sitting on weekdays during the last 7 days.  Include time spent at work, at home, while doing course work and during leisure time.  This may include time spent sitting at a desk, visiting friends, reading, or ": "sitting-time"
}
df = df.rename(columns=activity_set)
for key, value in activity_set.items():
    column_comments[value] = key
column_comments["sleep-qality"] = "1: very bad, 5: very good"


def parse_time(value, hours_to_minutes_limit=5):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().lower()
    if s in ["", "-", "none"]:
        return pd.NA

    # Replace commas
    s = re.sub(r'^.*?by day,\s*','', s)
    s = s.replace(",", " ")
    # Normalize separators
    s = s.replace("by day", "")

    total = 0

    # Split multiple expressions
    parts = re.split(r"[;/,]| and ", s)

    for p in parts:
        p = p.strip()

        # Range: 1-2hrs
        if "-" in p and not re.search(r"\d{2}-\d{2}", p):
            try:
                a, b = map(float, re.findall(r"\d+\.?\d*", p))
                total += (a + b) / 2
                continue
            except:
                pass

        # x hours y minutes
        match = re.match(r"(\d+\.?\d*)\s*h.*?(\d+)\s*m", p)
        if match:
            h = float(match.group(1))
            m = float(match.group(2)) / 60
            total += h + m
            continue

        # x hour
        match = re.match(r"(\d+\.?\d*)\s*h", p)
        if match:
            total += float(match.group(1))
            continue

        # x minutes
        match = re.match(r"(\d+\.?\d*)\s*m", p)
        if match:
            total += float(match.group(1)) / 60
            continue

        # 90, 45, etc (just a number)
        if p.isdigit():
            n = int(p)
            if n <= hours_to_minutes_limit:
                total += n
            else:
                total += n / 60
            continue

        # floats like 1.5
        try:
            total += float(p)
            continue
        except:
            pass

    return total

df['vigorous-time'] = df['vigorous-time'].apply(parse_time)
df['days-moderate-activity'] = df['days-moderate-activity'].str.extract(r'(\d+)', expand=False)
df['moderate-time'] = df['moderate-time'].apply(parse_time)
df['days-walking-activity'] = df['days-walking-activity'].str.extract(r'(\d+)', expand=False)
df['walking-time'] = df['walking-time'].apply(parse_time)
df['sitting-time'] = df['sitting-time'].apply(lambda x: parse_time(x, hours_to_minutes_limit=24))
column_units["vigorous-time"] = column_units["moderate-time"] = column_units["walking-time"] = column_units["sitting-time"] = "hours"

print(df[['vigorous-time', "days-moderate-activity", 'moderate-time', "days-walking-activity", "walking-time", "sitting-time"]])


##### FOOD QUESTIONAIRE

rename_set = {
    "Dietary Habits Questions (14-item questionnaire for Adherence to Mediterranean diet)    Do you use olive oil as a main culinary fat?  ": "olive-oil-main-cooking-fat",
    "How much olive oil do you consume in a given day (including oil used for frying, salads, out-of-house meals, etc.)? ": "olive-oil-four-tbsp",
    "How many vegetable servings do you consume per day? (1 serving : 200 g [consider side dishes as half a serving])": "two-salad-servings",
    "How many fruit units (including natural fruit juices) do you consume per day?": "three-fruit-units",
    "How many servings of red meat, hamburger, or meat products (ham, sausage, etc.) do you consume per day? (1 serving: 100-150 g) ": "one-red-meat-serving",
    "How many servings of butter, margarine, or cream do you consume per day? (1 serving: 12 g) ": "one-butter-etc-serving",
    "How many sweet or carbonated beverages do you drink per day?": "one-beverage-per-day",
    "How much wine do you drink per week?": "seven-wine-glasses-weekly",
    "How many servings of legumes do you consume per week? (1 serving: 150 g)": "three-legumes-servings",
    "How many servings of fish or shellfish do you consume per week? (1 serving 100-150 g of fish or 4-5 units or 200 g of shellfish)": "three-fish-servings",
    "How many times per week do you consume commercial sweets or pastries (not homemade), such as cakes, cookies, biscuits, or custard? ": "three-pastries-servings",
    "How many servings of nuts (including peanuts) do you consume per week? (1 serving 30 g) ": "three-nuts-servings",
    "Do you preferentially consume chicken, turkey, or rabbit meat instead of veal, pork, hamburger, or sausage? ": "chicken-meat-preferred",
    "How many times per week do you consume vegetables, pasta, rice, or other dishes seasoned with sofrito (sauce made with tomato and onion, leek, or garlic and simmered with olive oil)? ": "two-sofrito-servings",
    "Pregnancy test done on women of child-bearing age? Report result": "pregnant"
}
df = df.rename(columns=rename_set)
for key, value in rename_set.items():
    column_comments[value] = key

def map_geq(x, n):
    if pd.isna(x):
        return np.nan
    x = x.lower().replace(" ", "")
    # Look for '<4'
    if f"<{n}" in x:
        return False
    # Look for '>4' or '≥4'
    if f">{n}" in x or f"≥{n}" in x or f"=>{n}" in x or f">={n}" in x:
        return True
    # Maybe someone wrote only "4"
    if x.startswith("4"):
        return True
    # fallback
    return np.nan

df['olive-oil-main-cooking-fat'] = df['olive-oil-main-cooking-fat'].map({'Yes': True, 'No': False}).astype('boolean')
df['chicken-meat-preferred'] = df['chicken-meat-preferred'].map({'Yes': True, 'No': False}).astype('boolean')


for col, n in {
    'olive-oil-four-tbsp': 4,
    'two-salad-servings': 2,
    'three-fruit-units': 3,
    'one-red-meat-serving': 1,
    'one-butter-etc-serving': 1,
    'one-beverage-per-day': 1,
    'seven-wine-glasses-weekly': 7,
    'three-legumes-servings': 3,
    "three-fish-servings": 3,
    "three-pastries-servings": 3,
    'three-nuts-servings': 3,
    'two-sofrito-servings': 2
}.items():
    column_comments[col] = column_comments[col] + f" - Greater or equal to {n} maps to True, less to False."
    df[col] = df[col].apply(lambda x: map_geq(x, n))



#### BODY CHARS
df['pregnant'] = df['pregnant'].str.lower().replace(" ", "").map({'yes': True, 'no': False, 'negative': False, "0": False, "yes,negative": False}).astype('boolean')
df.loc[df["gender"] != "Male", "pregnant"] = pd.NA

rename_set = {
    "Weight (kg)": "weight",
    "Height (cm)": "height",
    "BMI (>25 kg/m2)": "bmi"
}
df = df.rename(columns=rename_set)
column_units["weight"] = "kg"
column_units["height"] = "cm"
column_units["bmi"] = "kg/m^2"

#### YES-NO questionaire
rename_set = {
    "Raised Triglycerides ( ≥ 100 mg/dL (1.7 mmol/L))": "raised-triglycerides",
    "Reduced HDL cholesterol: < 40 mg/dL (1.03 mmol/L) in males or < 50 mg/dL (1.29mmol/L) in females. ": "reduced-hdl-cholesterol",
    "Raised blood pressure: systolic BP ≥ 130 or diastolic BP ≥ 85 mm Hg. ": "raised-blood-pressure",
    'Raised fasting plasma glucose (FPG): ≥ 90 mg/dL (5.0 mmol/L).   ': "raised-fpg",
    "Current smokers ": "current-smoker",
    "Do you have any of the following chronic medical conditions?        (choice=Diabetes)": "diabetes",
    "Do you have any of the following chronic medical conditions?        (choice=Hypertension)": "hypertension",
    "Do you have any of the following chronic medical conditions?        (choice=Hypertension with medication)": "hypertension-with-medication",
    "Do you have any of the following chronic medical conditions?        (choice=Dyslipidaemia (imbalance of lipids such as cholesterol, low-density lipoprotein cholesterol, (LDL-C), triglycerides, and high-density lipoprotein (HDL)).)": "dislipidaemia",
    "Do you have any of the following chronic medical conditions?        (choice=Dyslipidaemia controlled with medication)": "dislipidaemia-with-medication",
    "Do you have any of the following chronic medical conditions?        (choice=Cardiovascular disease)": "cardiovascular-disease",
    "Do you have any of the following chronic medical conditions?        (choice=Chronic gastrointestinal condition)": "chronic-gastrointestinal-condition",
    "Do you have any of the following chronic medical conditions?        (choice=Cancer)": "cancer",
    "Do you have any of the following chronic medical conditions?        (choice=Acute infectious disease)": "acute-infectious-disease",
    "Do you have any of the following chronic medical conditions?        (choice=Renal disease)": "renal-disease",
    "Do you have any of the following chronic medical conditions?        (choice=None that I am aware of)": "no-known-disease",
    "Do you take any current medication? (choice=ACE inhibitors)": "ace-inhibitors",
    "Do you take any current medication? (choice=Diuretics)": "diuretics",
    "Do you take any current medication? (choice=Other antihypertensive agents)": "other-antihypertensive-agents",
    "Do you take any current medication? (choice=Statins)": "statins",
    "Do you take any current medication? (choice=Other lipid-lowering agents)": "other-lipid-lowering-agents",
    "Do you take any current medication? (choice=Insulin)": "insulin",
    "Do you take any current medication? (choice=Oral hypoglycaemic agents)": "other-hypoglycaemic-agents",
    "Do you take any current medication? (choice=Aspiring or Antiplatelet therapy)": "aspiring-or-ontiplatelet-therapy",
    "Do you take any current medication? (choice=Hormone-replacement therapy)": "hormone-replacement-therapy",
    "Do you take any current medication? (choice=Pain medication)": "pain-medication",
    "Do you take any current medication? (choice=Antidepressants)": "antidepressants",
    "Do you take any current medication? (choice=Supplements (Vitamins, minerals, fatty acids, probiotics))": "supplements",
    "Do you take any current medication? (choice=Others)": "other-medication",
    "Do you take any current medication? (choice=None:)": "no-medication",
    "Have you used antibiotics in the past 3 months?": "antibiotics",
    "Do you have any food allergies?": "food-allergies",
    "Have you taken part in any research studies in the past 3 months?": "research-studies",
    "Have you lost or gained weight in the past 3 months? If yes, how much?": "weight-gain",
    "Do you currently suffer from any long-term illness?  If Yes, please specify.": "long-term-illness",
    'Are you pregnant, breast feeding, planning to get pregnant or your partner is planning to get pregnant, in the next 12 months?  ': "parenting"
}
df = df.rename(columns=rename_set)
for key, value in rename_set.items():
    column_comments[value] = key
df["detailed-info"] = ""


def parse_yes_no(value):
    if pd.isna(value) or value == "":
        return pd.NA, None
    s = str(value).strip().lower()
    # pure yes
    if s == "yes":
        return True, None
    # pure no
    if s == "no":
        return False, None
    # capture something like: yes: allergen, yes - asthma
    m = re.match(r'^(yes)?[\s:,-]*(.+)$', s)
    if m:
        extra = m.group(2).strip()
        return True, extra

    # fallback
    return pd.NA, None


details_list = []
for col in rename_set.values():
    parsed = df[col].apply(parse_yes_no)
    # overwrite column with True/False/None
    df[col] = parsed.apply(lambda x: x[0])
    # collect details
    detail = parsed.apply(lambda x: f"{col}: {x[1]}" if x[1] else None)
    details_list.append(detail)
df["detailed-info"] = (
    pd.concat(details_list, axis=1)
    .apply(lambda row: "; ".join([r for r in row if r is not None]), axis=1)
)


### FINAL CLEANUP
df = replace_empty_with_na(df)
df = column_names_remove_spaces(df)
df = column_names_to_lowercase(df)
df = column_names_remove_underscores(df)

df['visit'] = "V1"

for col in df.columns: print(f"\"{col}\", ")

string_cols = ["patient", "visit", "site", "place-of-birth", "place-of-residence", "gender", "ethnicity", "marital-status",
               "living-status", "employment-status", "profession", "salary", "working-time", "shift-patterns",
               "education-level", "smoking-status", "diet", "diet-description", "medical-history", "medical-history-other",
               "naps-descr", "ethnicity-subcategory", "detailed-info"]
int_cols = ["sleep-quality", "days-active", "days-moderate-activity", "days-walking-activity",
            "menarche-years", "menopause-years", "n-children", "n-pregnancies", "years-smoking", "years-withnout-smoking",
            "age-started-smoking"]
float_cols = ["sleep-workdays", "sleep-free-days", "vigorous-time", "moderate-time", "walking-time", "sitting-time",
              "weight", "height", "bmi", "years-working", "cigaretes-per-day"]
date_cols = ["date-of-birth"]
bool_cols = [s for s in df.columns if s not in string_cols + int_cols + float_cols + date_cols]
df = change_types(df, string_cols=string_cols, float_cols=float_cols, date_cols=date_cols)

categhorical_cols = ["visit", "gender", "ethnicity", "marital-status", "living-status", "employment-status", "salary",
                     "working-time", "education-level", "smoking-status", "diet", "medical-history"]

df = df[["patient", "visit", "site", "date-of-birth", "place-of-birth", "place-of-residence", "gender", "ethnicity", "ethnicity-subcategory",
         "marital-status", "living-status", "employment-status", "profession", "years-working", "salary", "working-time",
         "shift-patterns", "education-level", "menarche-years", "menopause-years", "n-children", "n-pregnancies",
         "currently-breastfeeding", "ever-breastfed",  "smoking-status", "cigaretes-per-day", "years-smoking", "years-withnout-smoking",
         "age-started-smoking",  "diet", "diet-description", "medical-history", "medical-history-other",
         "sleep-workdays", "sleep-free-days", "naps-during-day", "naps-descr", "sleep-quality", "days-active", "vigorous-time",
         "days-moderate-activity", "moderate-time", "days-walking-activity", "walking-time", "sitting-time", "olive-oil-main-cooking-fat",
         "olive-oil-four-tbsp", "two-salad-servings", "three-fruit-units", "one-red-meat-serving", "one-butter-etc-serving",
         "one-beverage-per-day", "seven-wine-glasses-weekly", "three-legumes-servings", "three-fish-servings", "three-pastries-servings",
         "three-nuts-servings", "chicken-meat-preferred", "two-sofrito-servings", "mediet-score", "pregnant", "weight", "height", "bmi",
         "raised-triglycerides", "reduced-hdl-cholesterol", "raised-blood-pressure", "raised-fpg", "current-smoker", "diabetes", "hypertension",
         "hypertension-with-medication", "dislipidaemia", "dislipidaemia-with-medication", "cardiovascular-disease", "chronic-gastrointestinal-condition",
         "cancer", "acute-infectious-disease", "renal-disease", "no-known-disease", "ace-inhibitors", "diuretics", "other-antihypertensive-agents",
         "statins", "other-lipid-lowering-agents", "insulin", "other-hypoglycaemic-agents", "aspiring-or-ontiplatelet-therapy",
         "hormone-replacement-therapy", "pain-medication", "antidepressants", "supplements", "other-medication", "no-medication",
         "antibiotics", "food-allergies", "research-studies", "weight-gain", "long-term-illness", "parenting", "detailed-info"]]

print(df.columns)

test_data_frame(df, numeric_column_names=True)

metadata = DataFrameMetadata(df, "1.3", comment=f"RedCap sociodemographic data", column_comments=column_comments)

save(metadata, f"redcap")

print(df.columns)
print(df.dtypes)
print(df)
