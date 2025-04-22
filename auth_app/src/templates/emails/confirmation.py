def confirmation_email(full_name, frontend_url, user_id):
    """Шаблон письма пользователю о регистрации."""
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Confirmation</title>
        </head>
        <body>
            <h1>Hello, {full_name}!</h1>
            <p>Thank you for registering. Please confirm your email by visiting the link below:</p>
            <a href="{frontend_url}/api/v1/signup/confirm/{user_id}/">Confirm Email</a>
            <p>If you did not register, please ignore this email.</p>
            <p>Best regards,<br>Your Movie teater</p>
        </body>
        </html>
    """
