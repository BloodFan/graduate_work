def reset_password_email(full_name, frontend_url, user_id):
    """Template email sent to the user for password reset confirmation."""
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Confirmation</title>
        </head>
        <body>
            <h1>Hello, {full_name}!</h1>
            <p>We have received a request to reset the password for your account.</p>
            <p>To confirm your password change, please click the link below:</p>
            <a href="{frontend_url}/api/v1/users/reset-password-confirmation/{user_id}/">Confirm Password Change</a>
            <p>If you did not request a password reset, please ignore this email.</p>
            <p>Best regards,<br>Your Movie Theater Team</p>
        </body>
        </html>
    """
