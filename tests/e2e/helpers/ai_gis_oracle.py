"""
AI Recommendation & PostGIS GIS Authoritative Oracle.
Implements reference math for:
1. Content-Based TF-IDF and Cosine Similarity, interaction weighting, Explainability, and Cold-start.
2. Geodesic distance (Haversine/PostGIS geography) nearest branch calculations.
"""

import math
import re
from typing import List, Dict, Any, Tuple, Optional


EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    using the Haversine formula (matches PostGIS ST_Distance(geography)).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def find_nearest_branch(
    user_lat: float,
    user_lon: float,
    branches: List[Dict[str, Any]]
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Find the nearest active branch to user coordinates.
    Returns: (branch_dict, distance_km)
    """
    active_branches = [b for b in branches if b.get("con_hoat_dong", True)]
    if not active_branches:
        return None

    best_branch = None
    min_dist = float("inf")

    for branch in active_branches:
        b_lat = branch.get("vi_do", branch.get("lat"))
        b_lon = branch.get("kinh_do", branch.get("lng"))
        if b_lat is None or b_lon is None:
            continue
        dist = haversine_distance_km(user_lat, user_lon, float(b_lat), float(b_lon))
        if dist < min_dist:
            min_dist = dist
            best_branch = branch

    if best_branch is not None:
        return best_branch, min_dist
    return None


INTERACTION_WEIGHTS = {
    "xem": 1,
    "yeu_thich": 2,
    "them_gio_hang": 3,
    "dat_mon": 4,
    "danh_gia": 5,
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize Vietnamese text string."""
    tokens = re.findall(r"\w+", text.lower(), re.UNICODE)
    return tokens


def compute_tfidf_cosine_recommendation(
    user_interactions: List[Dict[str, Any]],
    dishes: List[Dict[str, Any]],
    top_n: int = 6,
) -> List[Dict[str, Any]]:
    """
    Compute Content-Based TF-IDF and Cosine Similarity scores.
    If user_interactions is empty, applies Cold-Start popularity fallback.
    """
    # Filter available dishes
    available_dishes = [d for d in dishes if d.get("con_hang", True) and d.get("hien_thi", True)]
    if not available_dishes:
        return []

    # Cold-Start Fallback if user has no interactions
    if not user_interactions:
        # Score = 0.6 * (reviews / max_reviews) + 0.4 * (rating / 5.0)
        max_reviews = max([d.get("so_luot_danh_gia", 0) for d in available_dishes] or [1])
        if max_reviews == 0:
            max_reviews = 1

        scored = []
        for dish in available_dishes:
            reviews = dish.get("so_luot_danh_gia", 0)
            rating = dish.get("diem_danh_gia", 4.5)
            cold_score = 0.6 * (reviews / max_reviews) + 0.4 * (rating / 5.0)
            scored.append({
                "dish": dish,
                "score": round(cold_score, 4),
                "is_cold_start": True,
                "ly_do_goi_y": "Phổ biến hôm nay",
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

    # Calculate corpus vocab
    dish_tokens_map = {}
    doc_freq: Dict[str, int] = {}
    for dish in available_dishes:
        text_corpus = f"{dish.get('ten', '')} {dish.get('danh_muc', '')} {dish.get('mo_ta', '')} {dish.get('nguyen_lieu', '')} {dish.get('the', '')}"
        toks = tokenize(text_corpus)
        dish_tokens_map[dish["id"]] = toks
        unique_toks = set(toks)
        for t in unique_toks:
            doc_freq[t] = doc_freq.get(t, 0) + 1

    total_docs = len(available_dishes)
    # Compute TF-IDF vectors for dishes
    dish_vectors: Dict[int, Dict[str, float]] = {}
    for dish in available_dishes:
        d_id = dish["id"]
        toks = dish_tokens_map[d_id]
        tf: Dict[str, float] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, count in tf.items():
            idf = math.log((total_docs + 1) / (doc_freq.get(t, 1) + 1)) + 1.0
            val = (1.0 + math.log(count)) * idf
            vec[t] = val
            norm_sq += val * val
        norm = math.sqrt(norm_sq) or 1.0
        # Normalize
        dish_vectors[d_id] = {t: v / norm for t, v in vec.items()}

    # Compute User Profile Vector
    user_vec: Dict[str, float] = {}
    for interaction in user_interactions:
        d_id = interaction.get("mon_an_id")
        action = interaction.get("loai_tuong_tac", "xem")
        weight = INTERACTION_WEIGHTS.get(action, 1)
        if d_id in dish_vectors:
            for t, val in dish_vectors[d_id].items():
                user_vec[t] = user_vec.get(t, 0.0) + (val * weight)

    # Normalize user vector
    user_norm_sq = sum(v * v for v in user_vec.values())
    user_norm = math.sqrt(user_norm_sq) or 1.0
    for t in user_vec:
        user_vec[t] /= user_norm

    # Cosine Similarity
    recommendations = []
    for dish in available_dishes:
        d_id = dish["id"]
        d_vec = dish_vectors[d_id]
        score = sum(user_vec.get(t, 0.0) * d_vec.get(t, 0.0) for t in d_vec)

        # Generate Explainable reason
        ly_do = generate_explainable_tag(dish, user_vec)
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
    corpus = f"{dish.get('ten', '')} {dish.get('danh_muc', '')} {dish.get('mo_ta', '')}".lower()
    if "lẩu" in corpus or "hotpot" in corpus:
        return "Gợi ý vì bạn yêu thích các món lẩu ấm cúng"
    elif dish.get("do_cay", 0) > 0 or "cay" in corpus or "sa tế" in corpus:
        return "Phù hợp với khẩu vị thích món cay nồng của bạn"
    elif "nướng" in corpus or "bbq" in corpus or "hải sản" in corpus:
        return "Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"
    elif dish.get("la_mon_chay", False) or "chay" in corpus:
        return "Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"
    return "Phù hợp với khẩu vị và các món bạn thường chọn"
