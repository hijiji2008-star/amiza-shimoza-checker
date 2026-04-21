DISPATCH_KEYWORDS = [
    "派遣", "スタッフィング", "テンプ", "パーソル", "アデコ",
    "マンパワー", "リクルートスタッフ", "フルキャスト", "ランスタッド",
    "ウィルグループ", "アウトソーシング",
]

def is_dispatch(company_name: str, job_title: str) -> bool:
    text = company_name + job_title
    return any(kw in text for kw in DISPATCH_KEYWORDS)
