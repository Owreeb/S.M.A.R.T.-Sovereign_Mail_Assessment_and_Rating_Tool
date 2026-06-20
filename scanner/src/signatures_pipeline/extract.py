from src.db.models import MailSystemRole

class Signature():
    role : MailSystemRole
    software : str
    vendor : str
    vendor_country: str
    vendor_category : str
    vendor_country_rating : str
    open_source_rating : str
    vendor_category_rating : str
    

def extract_smtp():
    pass

def extract_imap():
    pass

def extract_pop():
    pass

def extract_mx():
    pass

