"""
Email alert utility for bot completion/failure notifications.

Sends an HTML email via SMTP when a bot run finishes or crashes.
Gracefully skips if SMTP configuration is missing.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from backend import config


def send_run_complete_email(
    run_id: int,
    status: str,
    total_processed: int,
    total_applied: int,
    total_skipped: int,
    total_failed: int,
    search_query: str,
    error_message: str | None = None,
    duration_seconds: float | None = None,
) -> bool:
    """
    Send an email notification when a bot run completes.

    Parameters
    ----------
    run_id : int
        The BotRun ID.
    status : str
        Final status: COMPLETED, STOPPED, ERRORED.
    total_processed, total_applied, total_skipped, total_failed : int
        Run counters.
    search_query : str
        The search query used.
    error_message : str | None
        Error details if status is ERRORED.
    duration_seconds : float | None
        Total run duration.

    Returns
    -------
    bool
        True if the email was sent, False otherwise.
    """
    if not config.EMAIL_ALERTS_ENABLED:
        print("[Email] Alerts not configured — skipping.")
        return False

    try:
        subject = f"[LinkedIn Bot] Run #{run_id} — {status}"

        # Format duration
        duration_str = "N/A"
        if duration_seconds is not None:
            minutes, seconds = divmod(int(duration_seconds), 60)
            hours, minutes = divmod(minutes, 60)
            duration_str = f"{hours}h {minutes}m {seconds}s"

        # Build HTML body
        status_color = {
            "COMPLETED": "#22c55e",
            "STOPPED": "#f59e0b",
            "ERRORED": "#ef4444",
        }.get(status, "#6b7280")

        html_body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e2e8f0; padding: 24px;">
            <div style="max-width: 560px; margin: 0 auto; background: #1a1d27; border-radius: 12px; padding: 24px; border: 1px solid #2d3748;">
                <h2 style="margin-top: 0; color: #f1f5f9;">
                    LinkedIn Automation Report
                </h2>

                <div style="display: inline-block; padding: 4px 12px; border-radius: 6px; background: {status_color}20; color: {status_color}; font-weight: 600; margin-bottom: 16px;">
                    {status}
                </div>

                <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                    <tr>
                        <td style="padding: 8px 0; color: #94a3b8;">Run ID</td>
                        <td style="padding: 8px 0; text-align: right;">#{run_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #94a3b8;">Search Query</td>
                        <td style="padding: 8px 0; text-align: right;">{search_query}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #94a3b8;">Duration</td>
                        <td style="padding: 8px 0; text-align: right;">{duration_str}</td>
                    </tr>
                    <tr style="border-top: 1px solid #2d3748;">
                        <td style="padding: 8px 0; color: #94a3b8;">Processed</td>
                        <td style="padding: 8px 0; text-align: right; font-weight: 600;">{total_processed}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #22c55e;">✓ Applied</td>
                        <td style="padding: 8px 0; text-align: right; color: #22c55e; font-weight: 600;">{total_applied}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #f59e0b;">⊘ Skipped</td>
                        <td style="padding: 8px 0; text-align: right; color: #f59e0b; font-weight: 600;">{total_skipped}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #ef4444;">✗ Failed</td>
                        <td style="padding: 8px 0; text-align: right; color: #ef4444; font-weight: 600;">{total_failed}</td>
                    </tr>
                </table>

                {"<div style='padding: 12px; background: #ef444420; border-radius: 8px; color: #fca5a5; margin-top: 12px;'><strong>Error:</strong> " + (error_message or "") + "</div>" if error_message else ""}

                <p style="margin-top: 20px; font-size: 12px; color: #64748b;">
                    Sent at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                </p>
            </div>
        </body>
        </html>
        """

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.SMTP_USER
        msg["To"] = config.ALERT_EMAIL_TO
        msg.attach(MIMEText(html_body, "html"))

        # Send via SMTP
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_USER, config.ALERT_EMAIL_TO, msg.as_string())

        print(f"[Email] Alert sent to {config.ALERT_EMAIL_TO}")
        return True

    except Exception as e:
        print(f"[Email] Failed to send alert: {e}")
        return False
