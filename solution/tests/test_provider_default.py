from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings


@override_settings(NEMO_CHECKS=False, MCP_TRANSPORT="inprocess-test")
class ProviderDefaultTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("default-provider-user")
        self.client.force_login(self.user)

    def test_new_chat_selects_qwen(self):
        response = self.client.get("/chatbot/")
        self.assertEqual(response.context["selected_provider"], "qwen")

    def test_existing_demo_selection_is_migrated_once(self):
        session = self.client.session
        session["action_provider"] = "mock"
        session.save()
        response = self.client.get("/chatbot/")
        self.assertEqual(response.context["selected_provider"], "qwen")
        self.assertTrue(self.client.session["qwen_default_applied"])

    def test_explicit_demo_choice_remains_available(self):
        self.client.get("/chatbot/")
        self.client.post("/chatbot/", {"provider":"mock", "message":"Hello"})
        response = self.client.get("/chatbot/")
        self.assertEqual(response.context["selected_provider"], "mock")

    def test_pre_update_demo_session_is_switched_to_qwen(self):
        session = self.client.session
        session["action_provider"] = "mock"
        session["qwen_default_applied"] = True
        session.save()
        self.assertEqual(self.client.get("/chatbot/").context["selected_provider"], "qwen")
