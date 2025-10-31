import requests
import pandas as pd
import wikipediaapi
import re
import matplotlib.pyplot as plt

# ========== 1️⃣ 从 Wikidata 拉取人物信息 ==========
print("📡 正在从 Wikidata 获取数据...")

url = "https://query.wikidata.org/sparql"
query = """
SELECT ?person ?personLabel ?occupationLabel ?sex_or_genderLabel ?sexual_orientationLabel WHERE {
  VALUES ?occupation { wd:Q82594 wd:Q131524 } # Computer scientist, Entrepreneur
  ?person wdt:P106 ?occupation.
  OPTIONAL { ?person wdt:P21 ?sex_or_gender. }           # sex or gender
  OPTIONAL { ?person wdt:P91 ?sexual_orientation. }      # sexual orientation
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 300
"""

r = requests.get(url, params={"format": "json", "query": query}, headers={"User-Agent": "Mozilla/5.0"})
r.raise_for_status()
data = r.json()

results = []
for item in data["results"]["bindings"]:
    results.append({
        "name": item.get("personLabel", {}).get("value", ""),
        "occupation": item.get("occupationLabel", {}).get("value", ""),
        "gender": item.get("sex_or_genderLabel", {}).get("value", ""),
        "orientation": item.get("sexual_orientationLabel", {}).get("value", ""),
        "wikidata_url": item.get("person", {}).get("value", "")
    })

df = pd.DataFrame(results)
print(f"✅ 已获取 {len(df)} 条数据")

# ========== 2️⃣ 过滤男性样本 ==========
male_df = df[df["gender"].str.lower() == "male"].copy()

# ========== 3️⃣ 从 Wikipedia 补全性取向 ==========
print("🔍 正在从 Wikipedia 补充缺失的性取向信息...")

wiki = wikipediaapi.Wikipedia("en")
keywords = [
    "gay", "lesbian", "bisexual", "queer",
    "transgender", "non-binary", "asexual", "pansexual", "homosexual"
]

def fetch_orientation(name, current_value):
    if current_value:  # Wikidata 已有值
        return current_value
    try:
        page = wiki.page(name)
        text = page.text.lower()
        for k in keywords:
            if re.search(r"\b" + re.escape(k) + r"\b", text):
                return k
    except Exception:
        return ""
    return ""

male_df["orientation_filled"] = male_df.apply(
    lambda row: fetch_orientation(row["name"], row["orientation"]), axis=1
)

# ========== 4️⃣ 标记 LGBT ==========
lgbt_keywords = [
    "homosexual", "gay", "lesbian", "bisexual", "queer",
    "transgender", "non-binary", "asexual", "pansexual"
]
male_df["is_LGBT"] = male_df["orientation_filled"].str.lower().apply(
    lambda x: any(k in x for k in lgbt_keywords) if isinstance(x, str) else False
)

# ========== 5️⃣ 统计结果 ==========
total = len(male_df)
lgbt_count = male_df["is_LGBT"].sum()
ratio = lgbt_count / total if total > 0 else 0

print("\n📊 统计结果：")
print(f"公开标注为男性的样本数: {total}")
print(f"其中公开或推断为 LGBT 的人数: {lgbt_count}")
print(f"占比: {ratio:.2%}")

# ========== 6️⃣ 可视化 ==========
plt.figure(figsize=(5,5))
plt.pie([lgbt_count, total - lgbt_count],
        labels=["LGBT", "Non-LGBT"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#ff69b4", "#87ceeb"])
plt.title("LGBT proportion among publicly male computer scientists & entrepreneurs")
plt.show()

plt.figure(figsize=(6,4))
plt.bar(["Non-LGBT", "LGBT"], [total - lgbt_count, lgbt_count], color=["#87ceeb", "#ff69b4"])
plt.title("Count of publicly male computer scientists & entrepreneurs by LGBT status")
plt.xlabel("Category")
plt.ylabel("Count")
plt.show()

# ========== 7️⃣ 保存结果 ==========
male_df.to_csv("wikidata_cs_with_wikipedia_orientation.csv", index=False)
print("💾 已保存补全数据为 wikidata_cs_with_wikipedia_orientation.csv")
