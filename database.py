import sqlite3
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

DATABASE_FILE = 'email_data.db'

def get_db_connection():
    """Create a database connection and return it"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database if it doesn't exist"""
    if not os.path.exists(DATABASE_FILE):
        logger.info(f"Creating new database: {DATABASE_FILE}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            english_job TEXT NOT NULL DEFAULT 'Trading Assistant',
            french_job TEXT NOT NULL DEFAULT 'Assistant Trader',
            company TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            formality TEXT DEFAULT 'formal',
            role TEXT NOT NULL DEFAULT 'Trading Assistant',
            cover_letter_language TEXT NOT NULL DEFAULT 'english',
            email_language TEXT NOT NULL DEFAULT 'french',
            processed BOOLEAN DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    else:
        logger.info(f"Database already exists: {DATABASE_FILE}")
        
        # Check if we need to update the schema
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(contacts)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Check for new fields
        schema_updated = False
        
        # Migrate job field to english_job and add french_job if necessary
        if 'job' in column_names and 'english_job' not in column_names:
            logger.info("Migration: Splitting job field into english_job and french_job")
            
            # Add the new columns
            cursor.execute("ALTER TABLE contacts ADD COLUMN english_job TEXT NOT NULL DEFAULT 'Trading Assistant'")
            cursor.execute("ALTER TABLE contacts ADD COLUMN french_job TEXT NOT NULL DEFAULT 'Assistant Trader'")
            
            # Copy existing job data to english_job
            cursor.execute("UPDATE contacts SET english_job = job")
            
            # Create a decent french translation for existing jobs
            cursor.execute("UPDATE contacts SET french_job = CASE WHEN job = 'Trading Assistant' THEN 'Assistant Trader' ELSE job END")
            
            schema_updated = True
        
        # Check if legacy name field exists but should be removed
        if 'name' in column_names:
            logger.info("Migration: Removing legacy name field")
            
            # Create a temporary table without the name field
            cursor.execute('''
            CREATE TABLE contacts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                english_job TEXT NOT NULL DEFAULT 'Trading Assistant',
                french_job TEXT NOT NULL DEFAULT 'Assistant Trader',
                company TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                title TEXT,
                formality TEXT DEFAULT 'formal',
                role TEXT NOT NULL DEFAULT 'Trading Assistant',
                cover_letter_language TEXT NOT NULL DEFAULT 'english',
                email_language TEXT NOT NULL DEFAULT 'french',
                processed BOOLEAN DEFAULT 0
            )
            ''')
            
            # Copy data from old table to new table
            if 'english_job' in column_names:
                cursor.execute('''
                INSERT INTO contacts_new (id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
                SELECT id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed FROM contacts
                ''')
            else:
                cursor.execute('''
                INSERT INTO contacts_new (id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
                SELECT id, email, job, job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed FROM contacts
                ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE contacts')
            cursor.execute('ALTER TABLE contacts_new RENAME TO contacts')
            
            schema_updated = True
        
        # Add english_job and french_job if not exists but job does
        if 'english_job' not in column_names and 'french_job' not in column_names and 'job' in column_names:
            logger.info("Adding english_job and french_job columns")
            
            # Create a temporary table with the new schema
            cursor.execute('''
            CREATE TABLE contacts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                english_job TEXT NOT NULL DEFAULT 'Trading Assistant',
                french_job TEXT NOT NULL DEFAULT 'Assistant Trader',
                company TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                title TEXT,
                formality TEXT DEFAULT 'formal',
                role TEXT NOT NULL DEFAULT 'Trading Assistant',
                cover_letter_language TEXT NOT NULL DEFAULT 'english',
                email_language TEXT NOT NULL DEFAULT 'french',
                processed BOOLEAN DEFAULT 0
            )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
            INSERT INTO contacts_new (id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
            SELECT id, email, job, job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed FROM contacts
            ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE contacts')
            cursor.execute('ALTER TABLE contacts_new RENAME TO contacts')
            
            schema_updated = True
        
        if 'first_name' not in column_names:
            logger.info("Adding first_name column to contacts table")
            cursor.execute("ALTER TABLE contacts ADD COLUMN first_name TEXT")
            schema_updated = True
        
        if 'last_name' not in column_names:
            logger.info("Adding last_name column to contacts table")
            cursor.execute("ALTER TABLE contacts ADD COLUMN last_name TEXT")
            schema_updated = True
        
        if 'title' not in column_names:
            logger.info("Adding title column to contacts table")
            cursor.execute("ALTER TABLE contacts ADD COLUMN title TEXT")
            schema_updated = True
        
        if 'formality' not in column_names:
            logger.info("Adding formality column to contacts table")
            cursor.execute("ALTER TABLE contacts ADD COLUMN formality TEXT DEFAULT 'formal'")
            schema_updated = True
        
        # Check for old language column
        if 'language' in column_names and 'cover_letter_language' not in column_names:
            logger.info("Migrating database schema: renaming 'language' to 'cover_letter_language'")
            
            # Create a temporary table with the new schema
            cursor.execute('''
            CREATE TABLE contacts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                english_job TEXT NOT NULL DEFAULT 'Trading Assistant',
                french_job TEXT NOT NULL DEFAULT 'Assistant Trader',
                company TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                title TEXT,
                formality TEXT DEFAULT 'formal',
                role TEXT NOT NULL DEFAULT 'Trading Assistant',
                cover_letter_language TEXT NOT NULL DEFAULT 'english',
                email_language TEXT NOT NULL DEFAULT 'french',
                processed BOOLEAN DEFAULT 0
            )
            ''')
            
            # Copy data from old table to new table
            if 'english_job' in column_names:
                cursor.execute('''
                INSERT INTO contacts_new (id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
                SELECT id, email, english_job, french_job, company, first_name, last_name, title, formality, role, language, mail_language, processed FROM contacts
                ''')
            else:
                cursor.execute('''
                INSERT INTO contacts_new (id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
                SELECT id, email, job, job, company, first_name, last_name, title, formality, role, language, mail_language, processed FROM contacts
                ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE contacts')
            cursor.execute('ALTER TABLE contacts_new RENAME TO contacts')
            
            schema_updated = True
        
        if schema_updated:
            conn.commit()
            logger.info("Database schema updated successfully")
        
        conn.close()

def get_all_records(id=None):
    """Get all records or a specific record by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if id is not None:
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (id,))
        record = cursor.fetchone()
        conn.close()
        return record
    else:
        cursor.execute('SELECT * FROM contacts')
        records = cursor.fetchall()
        conn.close()
        return records

def add_record(email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language):
    """Add a new record to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO contacts (email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, processed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language))
    
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"Added new record ID: {record_id} for {email}")
    return record_id

def update_record(id, email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language):
    """Update an existing record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE contacts 
    SET email = ?, english_job = ?, french_job = ?, company = ?, first_name = ?, last_name = ?, title = ?, formality = ?, role = ?, cover_letter_language = ?, email_language = ?, processed = 0
    WHERE id = ?
    ''', (email, english_job, french_job, company, first_name, last_name, title, formality, role, cover_letter_language, email_language, id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Updated record ID: {id}")
    return True

def delete_record(id):
    """Delete a record by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM contacts WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted record ID: {id}")
    return True

def mark_as_processed(id):
    """Mark a record as processed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE contacts SET processed = 1 WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Marked record ID: {id} as processed")
    return True 