import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import messenger


class MessengerTests(unittest.TestCase):
    @patch("messenger.smtplib.SMTP")
    def test_send_email_sends_plain_text_and_html(self, smtp):
        server = smtp.return_value.__enter__.return_value

        with (
            patch.object(messenger, "EMAIL_ADDRESS", "researcher@example.com"),
            patch.object(messenger, "EMAIL_SMTP_SERVER", "smtp.example.com"),
            patch.object(messenger, "EMAIL_APP_PASSWORD", "app-password"),
        ):
            messenger.send_email("Research report", "Plain report", "<p>HTML report</p>")

        smtp.assert_called_once_with("smtp.example.com", 587)
        server.starttls.assert_called_once_with()
        server.login.assert_called_once_with("researcher@example.com", "app-password")
        sent_message = server.send_message.call_args.args[0]
        self.assertEqual(sent_message["Subject"], "Research report")
        self.assertEqual(sent_message["From"], "researcher@example.com")
        self.assertEqual(sent_message["To"], "researcher@example.com")
        self.assertEqual(sent_message.get_body(("plain",)).get_content().strip(), "Plain report")
        self.assertIn("<p>HTML report</p>", sent_message.get_body(("html",)).get_content())

    @patch("messenger.requests.post")
    def test_push_posts_message_and_credentials(self, post):
        with (
            patch.object(messenger, "pushover_user", "user-token"),
            patch.object(messenger, "pushover_token", "app-token"),
        ):
            messenger.push("Research complete")

        post.assert_called_once_with(
            messenger.pushover_url,
            data={
                "user": "user-token",
                "token": "app-token",
                "message": "Research complete",
            },
        )


if __name__ == "__main__":
    unittest.main()
