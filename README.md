# Automated Email Sender with CV and Cover Letter Customization

This Flask-based application automatically sends personalized emails with customized CV and cover letter attachments from your Outlook email client. The app uses a database to manage contacts and can generate PDF documents with personalized content.

## Features

- Manage contacts with email, job position, company name, and other details
- Automatically generate personalized CVs and cover letters in PDF format
- Support for both English and French templates
- Automated email sending via Outlook (works with both classic and new Outlook)
- Track which emails have been sent

## Requirements

- Windows 11 with Outlook installed (classic or new "olk.exe")
- Python 3.8 or higher
- Microsoft Office (for docx to PDF conversion)

## Setup Instructions

1. Clone this repository to your local machine
2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```
4. Prepare your templates in the `templates` folder:

   - `cv.docx`: Your CV template with a placeholder `{{ role }}`
   - `cover_letter_french.docx`: French cover letter template with placeholders `{{ date }}`, `{{ job }}`, `{{ company }}`, and `{{ name }}`
   - `cover_letter_english.docx`: English cover letter template with placeholders `{{ date }}`, `{{ job }}`, `{{ company }}`, `{{ name }}`, and `{{ signature }}`
   - `mail_french.txt`: French email body template with placeholders `{{ name }}` and `{{ job }}`
   - `mail_english.txt`: English email body template with placeholders `{{ name }}` and `{{ job }}`
5. Run the application:

   ```
   python app.py
   ```
6. Access the web interface at http://127.0.0.1:5000/

## Usage

1. **Add Contacts**: Click on "Add New Contact" to add a new entry to the database.
2. **Manage Contacts**: View, edit, and delete contacts from the main screen.
3. **Send Emails**: Click on "Process All Emails" to generate documents and send emails to all non-processed contacts.

## Notes

- The application will automatically detect which version of Outlook you're using.
- Generated PDFs are stored in the `output` folder.
- Logs are written to the `logs` folder for debugging.
- The database is stored in `email_data.db` (SQLite).

## Customization

- You can modify the templates in the `templates` folder to match your specific needs.
- For French emails, if no name is provided, "Madame, Monsieur" is used as the default salutation.
- For English emails, if no name is provided, "Sir or Madam" is used with "Yours faithfully" as the signature. If a name is provided, "Yours sincerely" is used as the signature.
