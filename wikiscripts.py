import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Wikidata SPARQL endpoint ---
url = "https://query.wikidata.org/sparql"

# --- 2. 查询：计算机科学家 + 企业家 ---
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

# --- 3. 发出请求 ---
print("📡 正在从 Wikidata 获取数据...")
r = requests.get(url, params={"format": "json", "query": query}, headers={"User-Agent": "Mozilla/5.0"})
r.raise_for_status()
data = r.json()

# --- 4. 提取结果 ---
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
df.to_csv("wikidata_cs_gender_orientation.csv", index=False)
print(f"✅ 已获取 {len(df)} 条数据，保存为 wikidata_cs_gender_orientation.csv")

# --- 5. 仅保留公开为男性的样本 ---
male_df = df[df["gender"].str.lower() == "male"].copy()

# --- 6. 标记公开LGBT身份 ---
lgbt_keywords = ["homosexual", "gay", "lesbian", "bisexual", "queer", "transgender"]
male_df["is_LGBT"] = male_df["orientation"].str.lower().apply(
    lambda x: any(k in x for k in lgbt_keywords) if isinstance(x, str) else False
)

# --- 7. 统计 ---
total = len(male_df)
lgbt_count = male_df["is_LGBT"].sum()
ratio = lgbt_count / total if total > 0 else 0

print(f"\n📊 公开标注为男性的样本数: {total}")
print(f"🌈 其中公开标注为 LGBT 的人数: {lgbt_count}")
print(f"🔢 占比: {ratio:.2%}")

# --- 8. 可视化 ---
plt.figure(figsize=(5,5))
plt.pie([lgbt_count, total - lgbt_count],
        labels=["LGBT", "Non-LGBT"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#ff69b4", "#87ceeb"])
plt.title("Proportion of publicly male computer scientists & entrepreneurs who identify as LGBT")
plt.show()

# --- 9. 柱状图 ---
plt.figure(figsize=(6,4))
plt.bar(["Non-LGBT", "LGBT"], [total - lgbt_count, lgbt_count], color=["#87ceeb", "#ff69b4"])
plt.title("Count of publicly male computer scientists & entrepreneurs by LGBT status")
plt.xlabel("Category")
plt.ylabel("Count")
plt.show()
