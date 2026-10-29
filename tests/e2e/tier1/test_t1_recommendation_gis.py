"""
Tier 1: AI Recommendation & PostGIS GIS Feature Coverage Tests (T1_recommendation_gis)
Verifies:
1. Haversine geodesic distance calculation (equivalent to PostGIS ST_Distance(geography)).
2. Finding nearest branch from multi-branch GPS coordinates.
3. Inactive branches filtering in spatial queries.
4. Cold-start popularity recommendation fallback for new users.
5. Explainable recommendation tagging based on dish features.
"""

import unittest
from tests.e2e.helpers.ai_gis_oracle import (
    haversine_distance_km,
    find_nearest_branch,
    compute_tfidf_cosine_recommendation,
    generate_explainable_tag,
)


class TestTier1RecommendationGIS(unittest.TestCase):
    """Tier 1: AI Recommendation & GIS Tests"""

    def setUp(self):
        # Sample branches
        self.branches = [
            {
                "id": 1,
                "ten": "Chi nhánh Tân Bình",
                "lat": 10.7925,
                "lng": 106.6669,
                "con_hoat_dong": True,
            },
            {
                "id": 2,
                "ten": "Chi nhánh Quận 1",
                "lat": 10.7769,
                "lng": 106.7009,
                "con_hoat_dong": True,
            },
            {
                "id": 3,
                "ten": "Chi nhánh Quận 7",
                "lat": 10.7325,
                "lng": 106.7150,
                "con_hoat_dong": False,  # Closed
            },
        ]

        # Sample dishes
        self.dishes = [
            {
                "id": 101,
                "ten": "Lẩu riêu cua bắp bò",
                "danh_muc": "Lẩu",
                "mo_ta": "Lẩu riêu cua đồng thơm ngọt ăn kèm bắp bò tươi",
                "do_cay": 1,
                "so_luot_danh_gia": 85,
                "diem_danh_gia": 4.8,
                "con_hang": True,
                "hien_thi": True,
            },
            {
                "id": 102,
                "ten": "Gỏi bò bóp thấu",
                "danh_muc": "Khai vị",
                "mo_ta": "Gỏi bò bóp thấu chua cay vừa miệng",
                "do_cay": 2,
                "so_luot_danh_gia": 40,
                "diem_danh_gia": 4.5,
                "con_hang": True,
                "hien_thi": True,
            },
            {
                "id": 103,
                "ten": "Rau củ luộc kho quẹt",
                "danh_muc": "Món rau",
                "mo_ta": "Rau củ tươi luộc chấm kho quẹt đậm đà",
                "do_cay": 0,
                "la_mon_chay": True,
                "so_luot_danh_gia": 30,
                "diem_danh_gia": 4.2,
                "con_hang": True,
                "hien_thi": True,
            },
        ]

    def test_t1_recommendation_gis_01_haversine_distance(self):
        """Test 1: Verify distance calculation between known landmarks in Ho Chi Minh City."""
        # Tan Binh (10.7925, 106.6669) to District 1 (10.7769, 106.7009)
        dist = haversine_distance_km(10.7925, 106.6669, 10.7769, 106.7009)
        # Expected straight-line distance is ~4.0 - 4.5 km
        self.assertGreater(dist, 3.5)
        self.assertLess(dist, 5.0)

    def test_t1_recommendation_gis_02_nearest_branch_lookup(self):
        """Test 2: User at Tan Binh coordinates selects Tan Binh branch as nearest."""
        user_lat, user_lon = 10.7930, 106.6675  # 100 meters from branch 1
        nearest, dist_km = find_nearest_branch(user_lat, user_lon, self.branches)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest["id"], 1)
        self.assertLess(dist_km, 0.5)

    def test_t1_recommendation_gis_03_inactive_branch_filtered(self):
        """Test 3: User very close to District 7 closed branch gets routed to active branch instead."""
        user_lat, user_lon = 10.7320, 106.7155  # Next to branch 3 (closed)
        nearest, _ = find_nearest_branch(user_lat, user_lon, self.branches)
        self.assertIsNotNone(nearest)
        self.assertNotEqual(nearest["id"], 3, "Closed branch must not be selected as nearest")

    def test_t1_recommendation_gis_04_cold_start_popularity_ranking(self):
        """Test 4: User without prior interactions receives items ranked by popularity."""
        recommendations = compute_tfidf_cosine_recommendation(
            user_interactions=[],
            dishes=self.dishes,
            top_n=2,
        )
        self.assertEqual(len(recommendations), 2)
        # Top 1 should be dish 101 (85 reviews, 4.8 rating)
        self.assertEqual(recommendations[0]["dish"]["id"], 101)
        self.assertTrue(recommendations[0]["is_cold_start"])
        self.assertEqual(recommendations[0]["ly_do_goi_y"], "Phổ biến hôm nay")

    def test_t1_recommendation_gis_05_explainable_tag_generation(self):
        """Test 5: Explainable tag generator highlights dominant dish features."""
        tag_hotpot = generate_explainable_tag(self.dishes[0], {})
        self.assertIn("lẩu", tag_hotpot.lower())

        tag_spicy = generate_explainable_tag(self.dishes[1], {})
        self.assertIn("cay", tag_spicy.lower())

        tag_vegan = generate_explainable_tag(self.dishes[2], {})
        self.assertIn("chay", tag_vegan.lower())


if __name__ == "__main__":
    unittest.main()
