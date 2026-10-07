from dotenv import load_dotenv
import os
from messenger import send_email, push
from agents import Agent, function_tool, ModelSettings

load_dotenv(override=True)

MODEL_NAME = os.getenv("MODEL_NAME")
USE_EMAIL = os.getenv("USE_EMAIL", "True") == "True"

settings = ModelSettings(tool_choice="required")

@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
    """
    Send out an email with the given subject and body to all sales prospects
    
    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
    """
    if USE_EMAIL:
        send_email(subject, text_body, html_body)
    else:
        push(f"Subject: {subject}\n\n{text_body}")
    return "Email sent successfully"

INSTRUCTIONS = """
You are provided with a detailed report. Use your tool to send an email, converting the report into
a clean, well presented HTML email with an appropriate subject line.
"""

email_agent = Agent(name="Email Agent", instructions=INSTRUCTIONS, model=MODEL_NAME, tools=[send_email_tool])