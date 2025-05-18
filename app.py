import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from database import init_db, get_all_records, add_record, update_record, delete_record
from email_sender import process_email_queue, send_selected_emails
from document_processor import generate_cv, generate_cover_letter
from logging_config import setup_logging

# Set up logging first
setup_logging()

# Get logger for this module
logger = logging.getLogger('app')

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'templates'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['OUTPUT_DIR'] = 'output'

# Ensure output directory exists
if not os.path.exists(app.config['OUTPUT_DIR']):
    os.makedirs(app.config['OUTPUT_DIR'])

# Initialize database and log startup
init_db()
logger.info('Email automation application startup')

@app.route('/')
def index():
    logger.info("Rendering main page")
    records = get_all_records()
    return render_template('index.html', records=records)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        logger.info("Processing add record request")
        email = request.form['email']
        english_job = request.form.get('english_job', 'Trading Assistant')
        french_job = request.form.get('french_job', 'Assistant Trader')
        company = request.form['company']
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        title = request.form.get('title', '')
        formality = request.form.get('formality', 'formal')
        role = request.form.get('role', 'Trading Assistant')
        cover_letter_language = request.form.get('cover_letter_language', 'english')
        email_language = request.form.get('email_language', 'french')
        
        add_record(email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language)
        logger.info(f"Added new record for {email} at {company}")
        flash('Record added successfully!', 'success')
        return redirect(url_for('index'))
    
    logger.info("Rendering add page")
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        logger.info(f"Processing edit request for record {id}")
        email = request.form['email']
        english_job = request.form.get('english_job', 'Trading Assistant')
        french_job = request.form.get('french_job', 'Assistant Trader')
        company = request.form['company']
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        title = request.form.get('title', '')
        formality = request.form.get('formality', 'formal')
        role = request.form.get('role', 'Trading Assistant')
        cover_letter_language = request.form.get('cover_letter_language', 'english')
        email_language = request.form.get('email_language', 'french')
        
        update_record(id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language)
        logger.info(f"Updated record {id} for {email} at {company}")
        flash('Record updated successfully!', 'success')
        return redirect(url_for('index'))
    
    logger.info(f"Rendering edit page for record {id}")
    record = get_all_records(id)
    return render_template('edit.html', record=record)

@app.route('/delete/<int:id>')
def delete(id):
    logger.info(f"Processing delete request for record {id}")
    delete_record(id)
    logger.info(f"Deleted record {id}")
    flash('Record deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/send-emails')
def send_emails():
    logger.info("Starting email processing")
    records = get_all_records()
    results = process_email_queue(records)
    logger.info(f"Processed {len(results)} emails")
    flash(f'Processed {len(results)} emails. Check logs for details.', 'info')
    return redirect(url_for('index'))

@app.route('/select-emails', methods=['GET', 'POST'])
def select_emails():
    if request.method == 'POST':
        logger.info("Processing selected email send request")
        selected_ids = request.form.getlist('selected_records')
        
        if not selected_ids:
            flash('No records selected.', 'warning')
            return redirect(url_for('select_emails'))
        
        # Get all selected records
        selected_records = [get_all_records(int(id)) for id in selected_ids]
        
        # Filter out None values (in case a record was deleted)
        selected_records = [r for r in selected_records if r is not None]
        
        # Process selected records
        results = send_selected_emails(selected_records)
        logger.info(f"Processed {len(results)} selected emails")
        flash(f'Processed {len(results)} emails. Check logs for details.', 'info')
        return redirect(url_for('index'))
    
    logger.info("Rendering email selection page")
    records = get_all_records()
    return render_template('select_emails.html', records=records)

@app.route('/generate-cv', methods=['GET', 'POST'])
def standalone_cv():
    if request.method == 'POST':
        role = request.form.get('role', 'Trading Assistant')
        
        try:
            cv_path = generate_cv(role, app.config['OUTPUT_DIR'])
            logger.info(f"Successfully generated standalone CV for role: {role}")
            
            # Return the file for download
            return send_file(cv_path, as_attachment=True, download_name=f'CV - Justin Isambert.pdf')
        
        except Exception as e:
            logger.error(f"Error generating CV: {str(e)}")
            flash(f'Error generating CV: {str(e)}', 'danger')
            return redirect(url_for('standalone_cv'))
    
    return render_template('generate_cv.html')

@app.route('/generate-cover-letter', methods=['GET', 'POST'])
def standalone_cover_letter():
    if request.method == 'POST':
        language = request.form.get('language', 'english')
        english_job = request.form.get('english_job', 'Trading Assistant')
        french_job = request.form.get('french_job', 'Assistant Trader')
        company = request.form.get('company', '')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        title = request.form.get('title', '')
        formality = request.form.get('formality', 'formal')
        
        # Use the appropriate job title based on the selected language
        job = english_job if language == 'english' else french_job
        
        try:
            cl_path = generate_cover_letter(
                language, job, company, output_dir=app.config['OUTPUT_DIR'],
                first_name=first_name, last_name=last_name, title=title, formality=formality
            )
            logger.info(f"Successfully generated standalone cover letter for {company}, job: {job}")
            
            # Return the file for download
            return send_file(cl_path, as_attachment=True, download_name=f'Cover Letter - Justin Isambert.pdf')
        
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            flash(f'Error generating cover letter: {str(e)}', 'danger')
            return redirect(url_for('standalone_cover_letter'))
    
    return render_template('generate_cover_letter.html')

if __name__ == '__main__':
    app.run(debug=True) 