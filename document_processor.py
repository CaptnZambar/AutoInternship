import os
import logging
from datetime import datetime
from docxtpl import DocxTemplate
from docx2pdf import convert
import locale
import pythoncom

# Setup logging
logger = logging.getLogger(__name__)

def generate_cv(role, output_dir='output'):
    """
    Generate a CV with the provided role.
    """
    try:
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cv_template_path = os.path.join('templates', 'cv.docx')
        cv_output_docx = os.path.join(output_dir, 'CV_temp.docx')
        cv_output_pdf = os.path.join(output_dir, 'CV - Justin Isambert.pdf')
        
        # Create template object
        doc = DocxTemplate(cv_template_path)
        
        # Render the template with context
        context = {'role': role}
        doc.render(context)
        doc.save(cv_output_docx)
        
        # Initialize COM before calling Word automation
        pythoncom.CoInitialize()
        
        # Convert to PDF
        convert(cv_output_docx, cv_output_pdf)
        
        # Remove temporary docx file
        os.remove(cv_output_docx)
        
        logger.info(f"Successfully generated CV for role: {role}")
        return cv_output_pdf
    
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}")
        raise
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()

def get_current_date(language):
    """
    Return current date formatted according to the language.
    """
    if language.lower() == 'french':
        # Set locale to French to get French month names
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR')
            except:
                logger.warning("Could not set French locale, using default date format")
        
        # Format: "11 janvier 2023"
        return datetime.now().strftime("%d %B %Y")
    else:
        # Set locale to English
        try:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'en_US')
            except:
                logger.warning("Could not set English locale, using default date format")
        
        # Format: "January 11, 2023"
        return datetime.now().strftime("%B %d, %Y")

def generate_cover_letter(language, job, company, output_dir='output', first_name='', last_name='', title='', formality='formal'):
    """
    Generate a cover letter based on the language and provided details.
    """
    try:
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Determine which template to use based on language
        if language.lower() == 'french':
            template_path = os.path.join('templates', 'cover_letter_french.docx')
            
            # Set the appropriate salutation based on formality
            if formality == 'formal' and title and last_name:
                if title == 'Mr.':
                    recipient_name = f"Cher M. {last_name}"
                elif title == 'Ms.':
                    recipient_name = f"Chère Mme. {last_name}"
                else:
                    recipient_name = f"Cher {last_name}"
            elif formality == 'semi-formal' and first_name:
                if title == 'Ms.':
                    recipient_name = f"Chère {first_name}"
                else:
                    recipient_name = f"Cher {first_name}"
            else:
                recipient_name = "Madame, Monsieur"
            
            signature = None  # No signature for French version
        else:
            template_path = os.path.join('templates', 'cover_letter_english.docx')
            
            # Set the appropriate salutation based on formality
            if formality == 'formal' and title and last_name:
                recipient_name = f"Dear {title} {last_name}"
                signature = "Yours sincerely"
            elif formality == 'semi-formal' and first_name:
                recipient_name = f"Dear {first_name}"
                signature = "Yours sincerely"
            else:
                recipient_name = "Dear Sir or Madam"
                signature = "Yours faithfully"
        
        # Format output file names
        cl_output_docx = os.path.join(output_dir, 'CL_temp.docx')
        cl_output_pdf = os.path.join(output_dir, 'Cover Letter - Justin Isambert.pdf')
        
        # Create template object
        doc = DocxTemplate(template_path)
        
        # Prepare context for template rendering
        context = {
            'date': get_current_date(language),
            'job': job,
            'company': company,
            'name': recipient_name
        }
        
        # Add signature for English version
        if signature:
            context['signature'] = signature
        
        # Render the template with context
        doc.render(context)
        doc.save(cl_output_docx)
        
        # Initialize COM before calling Word automation
        pythoncom.CoInitialize()
        
        # Convert to PDF
        convert(cl_output_docx, cl_output_pdf)
        
        # Remove temporary docx file
        os.remove(cl_output_docx)
        
        logger.info(f"Successfully generated cover letter for {company}, job: {job}")
        return cl_output_pdf
    
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()

def get_email_template(language, job, role, first_name='', last_name='', title='', formality='formal'):
    """
    Return the email body text with placeholders replaced.
    """
    try:
        # Determine which template to use based on language
        if language.lower() == 'french':
            template_path = os.path.join('templates', 'mail_french.txt')
            
            # Set the appropriate salutation based on formality
            if formality == 'formal' and title and last_name:
                if title == 'Mr.':
                    recipient_name = f"Bonjour M. {last_name}"
                elif title == 'Ms.':
                    recipient_name = f"Bonjour Mme. {last_name}"
                else:
                    recipient_name = f"Bonjour {last_name}"
            elif formality == 'semi-formal' and first_name:
                recipient_name = f"Bonjour {first_name}"
            else:
                recipient_name = "Madame, Monsieur"
        else:  # English
            template_path = os.path.join('templates', 'mail_english.txt')
            
            # Set the appropriate salutation based on formality
            if formality == 'formal' and title and last_name:
                recipient_name = f"Dear {title} {last_name}"
            elif formality == 'semi-formal' and first_name:
                recipient_name = f"Dear {first_name}"
            else:
                recipient_name = "Dear Sir or Madam"
        
        # Read the template file
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # Split the template into object and body sections
        sections = template_content.split('#BODY')
        if len(sections) != 2:
            raise ValueError(f"Invalid email template format in {template_path}. Expected #OBJECT and #BODY sections.")
        
        object_section = sections[0].replace('#OBJECT', '').strip()
        body_section = sections[1].strip()
        
        # Replace placeholders in both sections
        email_object = object_section.replace('{{ name }}', recipient_name).replace('{{ job }}', job).replace('{{ role }}', role)
        email_body = body_section.replace('{{ name }}', recipient_name).replace('{{ job }}', job)
        
        return email_object, email_body
    
    except Exception as e:
        logger.error(f"Error fetching email template: {str(e)}")
        raise 