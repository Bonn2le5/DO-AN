#!/usr/bin/env python3
"""
Validation script for Pure-Python TF-IDF & Cosine Recommendation Algorithm.
Verifies all algorithmic requirements for Milestone 4 (Features 19-22).
"""
import math
import re
from collections import Counter
from typing import Dict, List, Any, Optional

INTERACTION_WEIGHTS = {
    "xem": 1,
    "yeu_thich": 2,
    "them_gio_hang": 3,
    "dat_mon": 4,
    "danh_gia": 5,
}

ALIAS_WEIGHTS = {
    "view": 1,
    "thich": 2,
    "like": 2,
    "favorite": 2,
    "gio_hang": 3,
    "cart": 3,
    "add_cart": 3,
    "dat_hang": 4,
    "order": 4,
    "review": 5,
    "rating": 5,
}

def get_interaction_weight(action: str) -> int:
    norm_action = str(action).lower().strip()
    return INTERACTION_WEIGHTS.get(norm_action, ALIAS_WEIGHTS.get(norm_action, 1))

def tokenize_vietnamese(text: str) -> List[str]:
    """Tokenize Vietnamese text with diacritics into lowercase word tokens."""
    if not text:
        return []
    return re.findall(r"[\wÀ-ỹ]+", text.lower())

def extract_dish_tokens(dish_data: Dict[str, Any]) -> List[str]:
    """Extract combined corpus tokens from dish attributes."""
    name = dish_data.get("ten", "") or dish_data.get("name", "")
    category = dish_data.get("danh_muc", "") or dish_data.get("category", "")
    short_desc = dish_data.get("mo_ta_ngan", "") or dish_data.get("short_description", "")
    full_desc = dish_data.get("mo_ta_chi_tiet", "") or dish_data.get("description", "")
    ingredients = dish_data.get("nguyen_lieu", [])
    if isinstance(ingredients, list):
        ingredients_str = " ".join(ingredients)
    else:
        ingredients_str = str(ingredients)
    tags = dish_data.get("the_mon_an", []) or dish_data.get("tags", [])
    if isinstance(tags, list):
        tags_str = " ".join(tags)
    else:
        tags_str = str(tags)
    
    # Feature enhancers
    extras = []
    if dish_data.get("la_mon_chay", False):
        extras.append("món chay ăn chay thanh đạm")
    spicy_level = dish_data.get("do_cay", 0) or dish_data.get("spicy_level", 0)
    if spicy_level > 0:
        extras.append("món cay vị cay sa tế")
        if spicy_level >= 2:
            extras.append("rất cay nồng")

    combined = f"{name} {category} {short_desc} {full_desc} {ingredients_str} {tags_str} {' '.join(extras)}"
    return tokenize_vietnamese(combined)

def compute_pure_python_tfidf_cosine(
    user_interactions: List[Dict[str, Any]],
    dishes: List[Dict[str, Any]],
    top_n: int = 6,
) -> List[Dict[str, Any]]:
    # Filter available dishes
    available_dishes = [
        d for d in dishes
        if d.get("con_hang", True) and d.get("hien_thi", True)
    ]
    if not available_dishes:
        return []

    # Cold-Start Popularity Fallback
    if not user_interactions:
        max_reviews = max([d.get("so_luot_danh_gia", 0) for d in available_dishes] or [1])
        if max_reviews <= 0:
            max_reviews = 1

        scored = []
        for dish in available_dishes:
            reviews = dish.get("so_luot_danh_gia", 0)
            rating = float(dish.get("diem_danh_gia", 4.5))
            # Safe composite score strictly in [0.0, 1.0]
            cold_score = 0.6 * (reviews / max_reviews) + 0.4 * (rating / 5.0)
            cold_score = min(1.0, max(0.0, cold_score))
            scored.append({
                "dish": dish,
                "score": round(cold_score, 4),
                "is_cold_start": True,
                "ly_do_goi_y": "Phổ biến hôm nay",
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    # Calculate tokens & document frequencies
    dish_tokens_map = {}
    doc_freq = Counter()
    for dish in available_dishes:
        toks = extract_dish_tokens(dish)
        d_id = dish.get("id")
        dish_tokens_map[d_id] = toks
        for t in set(toks):
            doc_freq[t] += 1

    total_docs = len(available_dishes)

    # Compute TF-IDF vectors for dishes
    dish_vectors = {}
    for dish in available_dishes:
        d_id = dish.get("id")
        toks = dish_tokens_map[d_id]
        tf = Counter(toks)
        vec = {}
        norm_sq = 0.0
        for t, count in tf.items():
            # Standard smoothed IDF + sublinear TF
            idf = math.log((total_docs + 1) / (doc_freq[t] + 1)) + 1.0
            val = (1.0 + math.log(count)) * idf
            vec[t] = val
            norm_sq += val * val
        norm = math.sqrt(norm_sq) or 1.0
        dish_vectors[d_id] = {t: v / norm for t, v in vec.items()}

    # Compute User Profile Vector
    user_vec = Counter()
    has_valid_interaction = False
    for inter in user_interactions:
        d_id = inter.get("mon_an_id") or inter.get("food_id") or inter.get("mon_an")
        action = inter.get("loai_tuong_tac") or inter.get("interaction_type") or "xem"
        weight = inter.get("trong_so") or get_interaction_weight(action)
        if d_id in dish_vectors:
            has_valid_interaction = True
            for t, val in dish_vectors[d_id].items():
                user_vec[t] += val * float(weight)

    if not has_valid_interaction or not user_vec:
        # Fallback to cold-start if user interactions did not match any current dishes
        return compute_pure_python_tfidf_cosine([], dishes, top_n)

    # L2 Normalize user vector
    user_norm_sq = sum(v * v for v in user_vec.values())
    user_norm = math.sqrt(user_norm_sq) or 1.0
    norm_user_vec = {t: v / user_norm for t, v in user_vec.items()}

    # Compute Cosine Similarity
    recommendations = []
    for dish in available_dishes:
        d_id = dish.get("id")
        d_vec = dish_vectors[d_id]
        # Dot product of normalized vectors = Cosine Similarity in [0.0, 1.0]
        score = sum(norm_user_vec.get(t, 0.0) * d_vec.get(t, 0.0) for t in d_vec)
        score = min(1.0, max(0.0, score))
        ly_do = generate_explainable_tag(dish, norm_user_vec)
        recommendations.append({
            "dish": dish,
            "score": round(score, 4),
            "is_cold_start": False,
            "ly_do_goi_y": ly_do,
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations[:top_n]

def generate_explainable_tag(dish: Dict[str, Any], user_profile_vec: Dict[str, float]) -> str:
    """Generate user-friendly explainable recommendation tag."""
    corpus = f"{dish.get('ten', '')} {dish.get('danh_muc', '')} {dish.get('mo_ta_ngan', '')} {dish.get('mo_ta_chi_tiet', '')} {dish.get('mo_ta', '')}".lower()
    if "lẩu" in corpus or "hotpot" in corpus:
        return "Gợi ý vì bạn yêu thích các món lẩu ấm cúng"
    elif dish.get("do_cay", 0) > 0 or "cay" in corpus or "sa tế" in corpus:
        return "Phù hợp với khẩu vị thích món cay nồng của bạn"
    elif "nướng" in corpus or "bbq" in corpus or "hải sản" in corpus:
        return "Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"
    elif dish.get("la_mon_chay", False) or "chay" in corpus:
        return "Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"
    return "Phù hợp với khẩu vị và các món bạn thường chọn"

if __name__ == "__main__":
    dishes = [
        {"id": 1, "ten": "Lẩu Thái Hải Sản", "danh_muc": "Lẩu", "mo_ta": "Lẩu tôm mực cay chua", "do_cay": 2, "diem_danh_gia": 4.8, "so_luot_danh_gia": 85},
        {"id": 2, "ten": "Bò Tơ Nướng Sa Tế", "danh_muc": "Món Nướng", "mo_ta": "Bò nướng than hoa đậm đà cay nồng", "do_cay": 1, "diem_danh_gia": 4.6, "so_luot_danh_gia": 40},
        {"id": 3, "ten": "Đậu Hũ Tứ Xuyên Chay", "danh_muc": "Món Chay", "mo_ta": "Đậu hũ nấm sốt chay thanh nhẹ", "la_mon_chay": True, "diem_danh_gia": 4.5, "so_luot_danh_gia": 20},
    ]

    # Test 1: Cold start
    cs_recs = compute_pure_python_tfidf_cosine([], dishes, top_n=2)
    assert len(cs_recs) == 2, f"Expected 2, got {len(cs_recs)}"
    assert cs_recs[0]["is_cold_start"] is True
    assert cs_recs[0]["dish"]["id"] == 1
    assert cs_recs[0]["score"] <= 1.0 and cs_recs[0]["score"] >= 0.0
    print("Test 1 Passed: Cold-start returns ranked dishes with score in [0.0, 1.0]")

    # Test 2: Personalized with interaction weights
    interactions = [
        {"mon_an_id": 1, "loai_tuong_tac": "dat_mon"},   # weight 4
        {"mon_an_id": 1, "loai_tuong_tac": "danh_gia"},  # weight 5
        {"mon_an_id": 2, "loai_tuong_tac": "yeu_thich"}, # weight 2
    ]
    p_recs = compute_pure_python_tfidf_cosine(interactions, dishes, top_n=3)
    assert p_recs[0]["is_cold_start"] is False
    assert p_recs[0]["dish"]["id"] == 1
    assert "lẩu" in p_recs[0]["ly_do_goi_y"].lower()
    for r in p_recs:
        assert 0.0 <= r["score"] <= 1.0, f"Score {r['score']} out of bounds"
    print("Test 2 Passed: Personalized recommendation correctly weights interactions and maintains [0.0, 1.0] bounds")

    # Test 3: Explainable tags
    assert "lẩu" in generate_explainable_tag(dishes[0], {}).lower()
    assert "cay" in generate_explainable_tag(dishes[1], {}).lower()
    assert "chay" in generate_explainable_tag(dishes[2], {}).lower()
    print("Test 3 Passed: Explainable tags match feature criteria")
    print("All algorithm tests passed successfully!")
