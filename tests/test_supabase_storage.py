import unittest
from unittest.mock import Mock, patch

import config
import services_helper
import sheets_helper
import supabase_helper


class SupabaseStorageTests(unittest.TestCase):
    def setUp(self):
        self.url = patch.object(config, "SUPABASE_URL", "https://example.supabase.co")
        self.key = patch.object(config, "SUPABASE_SERVICE_ROLE_KEY", "test-secret")
        self.url.start()
        self.key.start()
        self.addCleanup(self.url.stop)
        self.addCleanup(self.key.stop)

    @patch("supabase_helper.requests.request")
    def test_request_uses_server_credentials_and_rest_endpoint(self, mock_request):
        response = Mock()
        response.content = b"[]"
        response.json.return_value = []
        mock_request.return_value = response

        result = supabase_helper.request("GET", "admissions", params={"select": "*"})

        self.assertEqual(result, [])
        args, kwargs = mock_request.call_args
        self.assertEqual(args[:2], ("GET", "https://example.supabase.co/rest/v1/admissions"))
        self.assertEqual(kwargs["headers"]["apikey"], "test-secret")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-secret")
        self.assertEqual(kwargs["params"], {"select": "*"})
        self.assertEqual(kwargs["timeout"], 15)
        response.raise_for_status.assert_called_once_with()

    @patch("sheets_helper.supabase_helper.request")
    def test_admission_write_uses_supabase_when_configured(self, mock_request):
        row = sheets_helper.add_admission(
            {
                "student_name": "Asha",
                "course_name": "AutoCAD",
                "course_fees": 5500,
            }
        )

        self.assertEqual(row["Student Name"], "Asha")
        self.assertEqual(mock_request.call_args.args[:2], ("POST", "admissions"))
        self.assertEqual(mock_request.call_args.kwargs["payload"]["student_name"], "Asha")
        self.assertEqual(mock_request.call_args.kwargs["payload"]["course_name"], "AutoCAD")

    @patch("sheets_helper.supabase_helper.request")
    def test_recent_admissions_maps_database_fields_to_dashboard_fields(self, mock_request):
        mock_request.return_value = [
            {
                "timestamp": "2026-10-28 10:00:00",
                "student_name": "Asha",
                "course_name": "AutoCAD",
                "course_fees": "5500",
            }
        ]

        records = sheets_helper.get_recent_admissions(limit=5)

        self.assertEqual(records[0]["Student Name"], "Asha")
        self.assertEqual(records[0]["Course Name"], "AutoCAD")
        self.assertEqual(mock_request.call_args.kwargs["params"]["limit"], 5)

    @patch("services_helper.supabase_helper.request")
    def test_service_enquiry_write_uses_supabase_when_configured(self, mock_request):
        row = services_helper.save_enquiry(
            {
                "name": "Asha",
                "email": "asha@example.com",
                "phone": "123",
                "category": "IT",
                "service": "Website",
                "message": "Please contact me",
            }
        )

        self.assertEqual(row["Name"], "Asha")
        self.assertEqual(mock_request.call_args.args[:2], ("POST", "service_enquiries"))
        self.assertEqual(mock_request.call_args.kwargs["payload"]["email"], "asha@example.com")
        self.assertEqual(mock_request.call_args.kwargs["payload"]["service_required"], "Website")

    def test_partial_supabase_configuration_is_an_error(self):
        with patch.object(config, "SUPABASE_SERVICE_ROLE_KEY", ""):
            with self.assertRaisesRegex(RuntimeError, "Configure both"):
                supabase_helper.is_configured()


if __name__ == "__main__":
    unittest.main()
