# Password Reset Requirements

As a registered customer, I want to reset my password using a time-limited email link.
The link must expire after 15 minutes.
The link must not work after it has been used once.
The system should send the link to the email address associated with the account.

Additional concerns:
- The reset email should be rate-limited.
- The system should support both mobile and desktop browsers.
- The link should be invalid if the user requests a new password reset.

Note: The product team is still deciding whether the reset link should be single-use or token-bound to the session.
