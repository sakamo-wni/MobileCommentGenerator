import json
import logging
import os
from collections import Counter, defaultdict

import boto3
import pandas as pd

# ロガー設定
logger = logging.getLogger(__name__)

# 🔑 AWSプロファイル名を環境変数から取得（デフォルトなし）
aws_profile = os.getenv("AWS_PROFILE")
if aws_profile:
    session = boto3.Session(profile_name=aws_profile)
else:
    # デフォルト認証情報を使用
    session = boto3.Session()
s3 = session.client("s3")

# 📂 S3バケット情報
BUCKET = "it-literacy-457604437098-ap-northeast-1"
PREFIX = "downloaded_jsonl_files_archive/"

# 📁 出力フォルダ作成
os.makedirs("output/analysis", exist_ok=True)


# 🗓 カテゴリ分類関数
def classify_category(yyyymm: str) -> str:
    month = int(yyyymm[4:])
    if month in [3, 4, 5]:
        return "春"
    if month == 6:
        return "梅雨"
    if month in [7, 8]:
        return "夏"
    if month == 9:
        return "台風"
    if month in [10, 11]:
        return "秋"
    if month in [12, 1, 2]:
        return "冬"
    return "不明"


# 🎯 天候パターン分析器
class WeatherPatternAnalyzer:
    def __init__(self):
        self.patterns = {
            "sunny": ["晴", "陽", "日差し", "太陽", "青空", "快晴", "好天", "日射", "眩し", "まぶし"],
            "cloudy": ["雲", "曇", "どんより", "厚雲", "薄雲", "雲間", "雲海"],
            "rainy": ["雨", "傘", "濡れ", "湿", "じめじめ", "しとしと", "ザーザー", "ぽつぽつ", "降水", "レイン"],
            "stormy": ["雷", "雷雨", "突風", "暴風", "嵐", "荒天", "強風", "ゲリラ", "竜巻"],
            "mixed": ["変わり", "移ろ", "変化", "不安定", "ころころ", "たり", "一時", "のち"],
            "fog": ["霧", "もや", "かすみ", "霞", "視界", "靄", "ミスト"],
            "snow": ["雪", "雪化粧", "粉雪", "吹雪", "雪降", "積雪", "雪景色"],
            "hot": ["暑", "猛暑", "酷暑", "炎天", "熱中", "灼熱", "蒸し暑", "真夏日"],
            "cold": ["寒", "冷", "凍", "氷", "霜", "極寒", "厳寒", "真冬日"],
            "humid": ["湿", "ムシムシ", "じめじめ", "べたべた", "蒸し", "湿気"],
            "dry": ["乾燥", "カラカラ", "パサパサ", "乾い", "湿度低"],
            "wind": ["風", "そよ風", "微風", "強風", "突風", "無風", "風速", "ビル風"],
            "special": ["黄砂", "花粉", "紫外線", "UV", "オゾン", "PM2.5", "大気"],
        }

    def analyze_comment(self, comment: str) -> dict[str, bool]:
        return {p: any(k in comment for k in ks) for p, ks in self.patterns.items()}

    def get_missing_patterns(self, top_comments: list[str]) -> list[str]:
        counts = defaultdict(int)
        for c in top_comments:
            for p, found in self.analyze_comment(c).items():
                if found:
                    counts[p] += 1
        return [p for p, c in counts.items() if c < 2]


# 📊 コメント品質スコアリング
class CommentQualityScorer:
    def __init__(self):
        self.quality_indicators = {
            "具体性": ["具体的", "詳細", "明確", "はっきり", "しっかり"],
            "感情表現": ["気持ち", "快適", "爽やか", "心地", "楽し", "嬉し"],
            "行動提案": ["おすすめ", "注意", "気をつけ", "準備", "対策", "工夫"],
            "時間性": ["朝", "昼", "夕", "夜", "午前", "午後", "明け方", "夕方"],
            "地域性": ["海", "山", "都市", "郊外", "沿岸", "内陸", "平野", "盆地"],
        }
        self.negative_indicators = ["？？？", "不明", "エラー", "###", "NULL", "none"]

    def score_comment(self, comment: str, count: int) -> float:
        if any(neg in comment for neg in self.negative_indicators):
            return 0.0
        base = min(10.0, count / 1000)
        bonus = sum(1.0 for ks in self.quality_indicators.values() if any(k in comment for k in ks))
        length_bonus = 2.0 if 4 <= len(comment) <= 12 else 1.0 if 3 <= len(comment) <= 15 else 0.0
        return base + bonus + length_bonus


# 🌈 コメント抽出器
class SmartCommentExtractor:
    def __init__(self):
        self.analyzer = WeatherPatternAnalyzer()
        self.scorer = CommentQualityScorer()

    def extract_enhanced_comments(self, all_comments: list[str], current_top30: list[str], target_count: int = 100):
        current_set = set(current_top30)
        missing_patterns = self.analyzer.get_missing_patterns(current_top30)
        comment_counter = Counter(all_comments)
        candidates = []

        for comment, count in comment_counter.items():
            if comment in current_set:
                continue
            patterns = self.analyzer.analyze_comment(comment)
            score = self.scorer.score_comment(comment, count)
            missing_bonus = sum(5.0 for p in missing_patterns if patterns.get(p))
            total = score + missing_bonus
            candidates.append({"comment": comment, "count": count, "score": total, "patterns": patterns})

        candidates.sort(key=lambda x: x["score"], reverse=True)
        selected, pattern_counts = [], defaultdict(int)
        for c in candidates:
            if len(selected) >= target_count - 30:
                break
            if max((pattern_counts[p] for p, v in c["patterns"].items() if v), default=0) >= 3:
                continue
            selected.append(c)
            for p, v in c["patterns"].items():
                if v:
                    pattern_counts[p] += 1
        return selected


# 🧠 レポート生成
def generate_analysis_report(category: str, top30: list[str], enhanced: list[dict], comment_type: str) -> str:
    analyzer = WeatherPatternAnalyzer()
    current = defaultdict(int)
    for c in top30:
        for p, found in analyzer.analyze_comment(c).items():
            if found:
                current[p] += 1

    new = defaultdict(int)
    for c in enhanced:
        for p, found in c["patterns"].items():
            if found:
                new[p] += 1

    report = f"""\n# {category}の{comment_type}分析レポート\n\n## 現在のTOP30パターン分布\n"""
    for p, c in sorted(current.items()):
        report += f"- {p}: {c}件\n"

    report += """\n## 追加推奨コメント（例：上位20件 / 拡張コメント全体で100件）\n"""
    for i, c in enumerate(enhanced[:20], 1):
        ps = ", ".join([p for p, v in c["patterns"].items() if v])
        report += f"{i}. {c['comment']} (使用回数: {c['count']}, スコア: {c['score']:.1f})\n   パターン: {ps}\n"

    report += """\n## 追加後のパターン改善\n"""
    for p in analyzer.patterns:
        c = current[p]
        n = new[p]
        if n > 0:
            report += f"- {p}: {c}件 → {c + n}件 (+{n})\n"

    return report


# 🚀 メイン処理
def main():
    print("🚀 スマートコメント抽出器を開始...")
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    keys = [o["Key"] for o in response.get("Contents", []) if o["Key"].endswith(".jsonl")]

    weather_by_cat = defaultdict(list)
    advice_by_cat = defaultdict(list)

    for key in sorted(keys):
        yyyymm = key.split("/")[-1].replace(".jsonl", "")
        cat = classify_category(yyyymm)
        print(f"📂 {key} → {cat}")
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        lines = obj["Body"].read().decode("utf-8").splitlines()
        for line in lines:
            try:
                d = json.loads(line)
                wc = d.get("weather_comment", "").strip()
                adv = d.get("advice", "").strip()
                if wc:
                    weather_by_cat[cat].append(wc)
                if adv:
                    advice_by_cat[cat].append(adv)
            except json.JSONDecodeError as e:
                logger.warning(f"JSONDecodeError in line: {line[:50]}... Error: {e}")
                continue

    extractor = SmartCommentExtractor()

    for typ, dataset in [("weather_comment", weather_by_cat), ("advice", advice_by_cat)]:
        print(f"\n📈 {typ} の処理開始...")
        for cat, comments in dataset.items():
            if not comments:
                continue

            top30_tuples = Counter(comments).most_common(30)
            top30 = [c for c, _ in top30_tuples]
            enhanced = extractor.extract_enhanced_comments(comments, top30, target_count=100)

            df_top30 = pd.DataFrame(top30_tuples, columns=[typ, "count"])
            df_top30.to_csv(f"output/{cat}_{typ}_top30.csv", index=False, encoding="utf-8-sig")

            enhanced_tuples = [(c["comment"], c["count"]) for c in enhanced[:70]]
            all_combined = top30_tuples + enhanced_tuples
            df_all = pd.DataFrame(all_combined, columns=[typ, "count"])
            df_all.to_csv(f"output/{cat}_{typ}_enhanced100.csv", index=False, encoding="utf-8-sig")

            report = generate_analysis_report(cat, top30, enhanced, typ)
            with open(f"output/analysis/{cat}_{typ}_analysis.md", "w", encoding="utf-8") as f:
                f.write(report)

            print(f"✅ {cat}: 出力完了（Top30 + Enhanced100）")

    print("\n🎉 全処理完了！ output/ を確認してね！")


if __name__ == "__main__":
    main()
