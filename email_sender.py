import os
import logging
import win32com.client
import subprocess
import time
import pythoncom
import psutil
from document_processor import generate_cv, generate_cover_letter, get_email_template
from database import mark_as_processed

# Setup logging
logger = logging.getLogger(__name__)

# Path to Outlook Classic
OUTLOOK_CLASSIC_PATH = r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"

# Outlook account settings
OUTLOOK_ACCOUNT = "justin.isambert@edhec.com"

def is_new_outlook_running():
    """Check if the new version of Outlook (olk.exe) is running"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == 'olk.exe':
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking if new Outlook is running: {str(e)}")
        return False

def close_new_outlook():
    """Close the new version of Outlook (olk.exe) if it's running"""
    try:
        if is_new_outlook_running():
            logger.info("Closing Outlook New (olk.exe)")
            subprocess.run(['taskkill', '/F', '/IM', 'olk.exe'], check=True)
            # Give it a moment to close
            time.sleep(2)
            return True
        return False
    except Exception as e:
        logger.error(f"Error closing Outlook New: {str(e)}")
        return False

def is_outlook_classic_running():
    """Check if Outlook Classic is running"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == 'outlook.exe':
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking if Outlook Classic is running: {str(e)}")
        return False

def start_outlook_classic():
    """Start Outlook Classic if it's not already running"""
    try:
        if not is_outlook_classic_running():
            logger.info("Starting Outlook Classic")
            subprocess.Popen([OUTLOOK_CLASSIC_PATH])
            # Give it a moment to start
            time.sleep(5)
            return True
        return False
    except Exception as e:
        logger.error(f"Error starting Outlook Classic: {str(e)}")
        return False

def send_email(to_email, subject, body, attachments=None):
    """
    Send an email using Outlook Classic with specific account.
    
    Parameters:
    - to_email: Email address of the recipient
    - subject: Subject line of the email
    - body: Body text of the email
    - attachments: List of file paths to attach
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        # Close Outlook New if it's running
        close_new_outlook()
        
        # Ensure Outlook Classic is running
        start_outlook_classic()
        
        # Initialize COM
        pythoncom.CoInitialize()
        
        # Connect to Outlook
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        
        # Get the specific account
        for account in namespace.Accounts:
            if account.DisplayName == OUTLOOK_ACCOUNT:
                logger.info(f"Using Outlook account: {OUTLOOK_ACCOUNT}")
                break
        else:
            logger.error(f"Could not find Outlook account: {OUTLOOK_ACCOUNT}")
            return False
        
        # Create mail item
        mail = outlook.CreateItem(0)  # 0 = olMailItem
        
        # Set the sending account
        mail._oleobj_.Invoke(*(64209, 0, 8, 0, account))  # Set the SendUsingAccount property
        
        # Set email properties
        mail.To = to_email
        mail.Subject = subject
        mail.Body = body
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    mail.Attachments.Add(os.path.abspath(attachment))
                    logger.info(f"Added attachment: {attachment}")
                else:
                    logger.warning(f"Attachment not found: {attachment}")
        
        # Send the email
        mail.Send()
        
        logger.info(f"Email sent to {to_email} using account {OUTLOOK_ACCOUNT}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending email via Outlook Classic: {str(e)}")
        return False
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()

def process_single_record(record, output_dir='output'):
    """
    Process a single record from the database and send an email.
    
    Parameters:
    - record: Database record to process
    - output_dir: Directory to store generated files
    
    Returns:
    - Result dictionary with status information
    """
    try:
        record_id = record['id']
        email = record['email']
        
        # Get language-specific job titles
        english_job = record['english_job'] if 'english_job' in record.keys() else record['job'] 
        french_job = record['french_job'] if 'french_job' in record.keys() else record['job']
        
        company = record['company']
        first_name = record['first_name'] if 'first_name' in record.keys() else ''
        last_name = record['last_name'] if 'last_name' in record.keys() else ''
        title = record['title'] if 'title' in record.keys() else ''
        formality = record['formality'] if 'formality' in record.keys() else 'formal'
        role = record['role']
        cover_letter_language = record['cover_letter_language']
        email_language = record['email_language']
        processed = record['processed']
        
        # Skip already processed records
        if processed:
            logger.info(f"Skipping already processed record ID: {record_id}")
            return {"id": record_id, "status": "skipped", "message": "Already processed"}
        
        logger.info(f"Processing record ID: {record_id}, email: {email}")
        
        # Use the appropriate job title based on language
        job_for_cover_letter = english_job if cover_letter_language == 'english' else french_job
        job_for_email = english_job if email_language == 'english' else french_job
        
        # Generate documents
        cv_path = generate_cv(role, output_dir)
        cover_letter_path = generate_cover_letter(
            cover_letter_language, job_for_cover_letter, company, output_dir=output_dir,
            first_name=first_name, last_name=last_name, title=title, formality=formality
        )
        
        # Get email content with subject and body using email_language
        email_subject, email_body = get_email_template(
            email_language, job_for_email, role, 
            first_name=first_name, last_name=last_name, title=title, formality=formality
        )
        
        # Send email with attachments
        attachments = [cv_path, cover_letter_path]
        email_sent = send_email(email, email_subject, email_body, attachments)
        
        if email_sent:
            # Mark record as processed
            mark_as_processed(record_id)
            result = {"id": record_id, "status": "success", "message": "Email sent successfully"}
            logger.info(f"Successfully processed record ID: {record_id}")
        else:
            result = {"id": record_id, "status": "error", "message": "Failed to send email"}
            logger.error(f"Failed to send email for record ID: {record_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing record: {str(e)}")
        try:
            record_id = record['id'] if record and 'id' in record.keys() else 'unknown'
        except:
            record_id = 'unknown'
        return {"id": record_id, "status": "error", "message": str(e)}

def process_email_queue(records, output_dir='output'):
    """
    Process records from the database and send emails.
    
    Parameters:
    - records: List of database records to process
    - output_dir: Directory to store generated files
    
    Returns:
    - List of results for each record processed
    """
    results = []
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for record in records:
        try:
            result = process_single_record(record, output_dir)
            results.append(result)
            
            # Add a small delay between emails to avoid rate limiting
            time.sleep(2)
        
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            try:
                record_id = record['id'] if record and 'id' in record.keys() else 'unknown'
            except:
                record_id = 'unknown'
            results.append({"id": record_id, "status": "error", "message": str(e)})
    
    return results

def send_selected_emails(selected_records, output_dir='output'):
    """
    Process selected records from the database and send emails.
    
    Parameters:
    - selected_records: List of specific database records to process
    - output_dir: Directory to store generated files
    
    Returns:
    - List of result dictionaries with status information
    """
    results = []
    
    try:
        # Process each record
        for record in selected_records:
            result = process_single_record(record, output_dir)
            results.append(result)
            
            # If an error occurred, log it but continue processing
            if result['status'] == 'error':
                logger.error(f"Error processing record ID {result['id']}: {result['message']}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error processing selected emails: {str(e)}")
        return results 