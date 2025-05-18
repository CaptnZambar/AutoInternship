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
            job TEXT NOT NULL DEFAULT 'Trading Assistant',
            company TEXT NOT NULL,
            name TEXT,
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
        
        # Check if the old 'language' column exists and 'cover_letter_language' doesn't
        cursor.execute("PRAGMA table_info(contacts)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'language' in column_names and 'cover_letter_language' not in column_names:
            logger.info("Migrating database schema: renaming 'language' to 'cover_letter_language'")
            
            # Create a temporary table with the new schema
            cursor.execute('''
            CREATE TABLE contacts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                job TEXT NOT NULL DEFAULT 'Trading Assistant',
                company TEXT NOT NULL,
                name TEXT,
                role TEXT NOT NULL DEFAULT 'Trading Assistant',
                cover_letter_language TEXT NOT NULL DEFAULT 'english',
                email_language TEXT NOT NULL DEFAULT 'french',
                processed BOOLEAN DEFAULT 0
            )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
            INSERT INTO contacts_new (id, email, job, company, name, role, cover_letter_language, email_language, processed)
            SELECT id, email, job, company, name, role, language, mail_language, processed FROM contacts
            ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE contacts')
            cursor.execute('ALTER TABLE contacts_new RENAME TO contacts')
            
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

def add_record(email, job, company, name, role, cover_letter_language, email_language):
    """Add a new record to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO contacts (email, job, company, name, role, cover_letter_language, email_language, processed)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    ''', (email, job, company, name, role, cover_letter_language, email_language))
    
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    logger.info(f"Added new record ID: {record_id} for {email}")
    return record_id

def update_record(id, email, job, company, name, role, cover_letter_language, email_language):
    """Update an existing record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE contacts 
    SET email = ?, job = ?, company = ?, name = ?, role = ?, cover_letter_language = ?, email_language = ?, processed = 0
    WHERE id = ?
    ''', (email, job, company, name, role, cover_letter_language, email_language, id))
    
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