from django.test import TestCase
from rest_framework.test import APIClient
from .models import ChiNhanh, Branch
from .services import haversine_distance_km, find_nearest_branches
from .serializers import ChiNhanhSerializer


class ChiNhanhGISTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.b_tb = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Tân Bình",
            dia_chi="123 Hoàng Văn Thụ, Tân Bình, TP.HCM",
            so_dien_thoai="028 3811 1111",
            toa_do_gis="106.6669,10.7925",
            con_hoat_dong=True,
        )
        self.b_q1 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 1",
            dia_chi="45 Pasteur, Quận 1, TP.HCM",
            so_dien_thoai="028 3822 2222",
            toa_do_gis="106.7009,10.7769",
            con_hoat_dong=True,
        )
        self.b_q7 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 7",
            dia_chi="78 Nguyễn Thị Thập, Quận 7, TP.HCM",
            so_dien_thoai="028 3877 7777",
            toa_do_gis="106.7150,10.7325",
            con_hoat_dong=False,  # Inactive
        )

    def test_model_coordinate_properties(self):
        self.assertAlmostEqual(self.b_tb.kinh_do, 106.6669)
        self.assertAlmostEqual(self.b_tb.vi_do, 10.7925)
        self.assertAlmostEqual(self.b_tb.lng, 106.6669)
        self.assertAlmostEqual(self.b_tb.lat, 10.7925)
        self.assertAlmostEqual(self.b_tb.longitude, 106.6669)
        self.assertAlmostEqual(self.b_tb.latitude, 10.7925)

    def test_haversine_distance(self):
        dist = haversine_distance_km(10.7925, 106.6669, 10.7769, 106.7009)
        self.assertGreater(dist, 3.5)
        self.assertLess(dist, 5.0)

    def test_find_nearest_service(self):
        # Coordinates ~100m from Tan Binh branch
        branches = find_nearest_branches(10.7930, 106.6675, limit=1)
        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0].id, self.b_tb.id)
        self.assertLess(branches[0].distance_km, 0.5)

    def test_inactive_branch_filtered(self):
        # User very close to closed Q7 branch
        branches = find_nearest_branches(10.7320, 106.7155, limit=1)
        self.assertEqual(len(branches), 1)
        self.assertNotEqual(branches[0].id, self.b_q7.id)

    def test_api_nearest_endpoint(self):
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], self.b_tb.id)
        self.assertIn("distance_km", data)
        self.assertLess(data["distance_km"], 0.5)

    def test_api_nearest_vn_alias(self):
        resp = self.client.get("/api/chi-nhanh/nearest/", {"vi_do": 10.7930, "kinh_do": 106.6675})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], self.b_tb.id)

    def test_api_tim_gan_nhat_endpoint(self):
        resp = self.client.get("/api/chi-nhanh/tim-gan-nhat/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], self.b_tb.id)

    def test_api_nearest_missing_coords(self):
        resp = self.client.get("/api/branches/nearest/")
        self.assertEqual(resp.status_code, 400)

    def test_api_nearest_return_all(self):
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675, "all": "true"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # only active branches
        self.assertEqual(data[0]["id"], self.b_tb.id)
        self.assertEqual(data[1]["id"], self.b_q1.id)

    def test_api_list_proximity_sorting(self):
        resp = self.client.get("/api/branches/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # In DRF, standard list may be paginated or array
        results = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertIsInstance(results, list)
        self.assertEqual(results[0]["id"], self.b_tb.id)
