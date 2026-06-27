from pathlib import Path
p = Path('app.py')
text = p.read_text()
needle = 'from email.mime.multipart import MIMEMultipart\n\n# Load environment variables from .env if available'
replacement = 'from email.mime.multipart import MIMEMultipart\n\nfrom lab_programs import init_lab_programs_db\n\n# Load environment variables from .env if available'
if 'from lab_programs import init_lab_programs_db' not in text:
    text = text.replace(needle, replacement)
p.write_text(text)
