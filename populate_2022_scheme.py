import sqlite3
import os

DATABASE = 'studynova.db'

def init_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_scheme(conn, name, description):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM schemes WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    cursor.execute("INSERT INTO schemes (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    return cursor.lastrowid

def get_or_create_semester(conn, scheme_id, semester_number, name):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = ?", (scheme_id, semester_number))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    cursor.execute("INSERT INTO semesters (scheme_id, semester_number, name) VALUES (?, ?, ?)", 
                  (scheme_id, semester_number, name))
    conn.commit()
    return cursor.lastrowid

def get_or_create_branch(conn, name, code):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM branches WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    cursor.execute("INSERT INTO branches (name, code) VALUES (?, ?)", (name, code))
    conn.commit()
    return cursor.lastrowid

def add_subject(conn, scheme_id, semester_id, branch_id, code, name, stream=None, is_common=0):
    cursor = conn.cursor()
    # Check if subject already exists
    cursor.execute('''
        SELECT id FROM subjects 
        WHERE scheme_id = ? AND semester_id = ? AND branch_id = ? AND code = ?
    ''', (scheme_id, semester_id, branch_id, code))
    row = cursor.fetchone()
    if row:
        print(f"Subject {code} - {name} already exists")
        return row['id']
    
    cursor.execute('''
        INSERT INTO subjects 
        (scheme_id, semester_id, branch_id, name, code, stream, is_common) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (scheme_id, semester_id, branch_id, name, code, stream, is_common))
    conn.commit()
    print(f"Added subject: {code} - {name}")
    return cursor.lastrowid

def add_common_subjects(conn, scheme_id, semester_id, branch_ids):
    pass

def populate(conn=None):
    if conn is None:
        conn = init_connection()
    
    # Create 2022 scheme
    scheme_id = get_or_create_scheme(conn, '2022 Scheme', 'VTU 2022 Scheme for Engineering')
    
    # Get semesters 1-7 for 2022 scheme
    semesters = {}
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM semesters WHERE scheme_id = ?", (scheme_id,))
    for sem in cursor.fetchall():
        semesters[sem['semester_number']] = sem['id']
    
    # Get branches by code
    branches = {}
    cursor.execute("SELECT * FROM branches")
    for branch in cursor.fetchall():
        code = branch['code']
        branches[code] = branch['id']
    
    # CSE Subjects
    print("\n--- CSE Subjects ---")
    # 3rd Semester
    cse_3rd = [
        ('BCS301', 'Mathematics for Computer Science'),
        ('BCS302', 'Digital Design & Computer Organization'),
        ('BCS303', 'Operating Systems'),
        ('BCS304', 'Data Structures and Applications'),
        ('BCSL305', 'Data Structures Lab'),
        ('BCS306A', 'Object Oriented Programming with Java'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BCSL358A', 'Data Analytics with Excel'),
        ('BCSL358B', 'R Programming'),
        ('BCSL358C', 'Project Management with Git'),
        ('BCSL358D', 'Data Visualization with Python')
    ]
    for code, name in cse_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE'], code, name, stream='computer_science')
    
    # 4th Semester
    cse_4th = [
        ('BCS401', 'Analysis & Design of Algorithms'),
        ('BCS402', 'Microcontrollers'),
        ('BCS403', 'Database Management Systems'),
        ('BCSL404', 'Analysis & Design of Algorithms Lab'),
        ('BCS405A', 'Discrete Mathematical Structures'),
        ('BCS405B', 'Graph Theory'),
        ('BCS405C', 'Optimization Technique'),
        ('BCS405D', 'Linear Algebra'),
        ('BCS456A', 'Green IT and Sustainability'),
        ('BCS456B', 'Capacity Planning for IT'),
        ('BCS456C', 'UI/UX'),
        ('BCSL456D', 'Technical Writing using LaTeX'),
        ('BBOC407', 'Biology for Computer Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in cse_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE'], code, name, stream='computer_science')
    
    # 5th Semester
    cse_5th = [
        ('BCS501', 'Software Engineering & Project Management'),
        ('BCS502', 'Computer Networks'),
        ('BCS503', 'Theory of Computation'),
        ('BCSL504', 'Web Technology Lab'),
        ('BCS515A', 'Computer Graphics'),
        ('BCS515B', 'Artificial Intelligence'),
        ('BCS515C', 'Unix System Programming'),
        ('BCS515D', 'Distributed Systems'),
        ('BCS586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BCS508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in cse_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE'], code, name, stream='computer_science')
    
    # 6th Semester
    cse_6th = [
        ('BCS601', 'Cloud Computing'),
        ('BCS602', 'Machine Learning'),
        ('BCS613A', 'Blockchain Technology'),
        ('BCS613B', 'Computer Vision'),
        ('BCS613C', 'Compiler Design'),
        ('BCS613D', 'Advanced Java'),
        ('BCS654A', 'Introduction to Data Structures'),
        ('BCS654B', 'Fundamentals of Operating Systems'),
        ('BIS654C', 'Mobile Application Development'),
        ('BAI654D', 'Introduction to Artificial Intelligence'),
        ('BCS685', 'Project Phase-I'),
        ('BCSL606', 'Machine Learning Lab'),
        ('BISL657A', 'Tosca Automated Software Testing'),
        ('BCSL657B', 'React'),
        ('BAIL657C', 'Generative AI'),
        ('BCSL657D', 'DevOps'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in cse_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE'], code, name, stream='computer_science')
    
    # 7th Semester
    cse_7th = [
        ('BCS701', 'Internet of Things'),
        ('BCS702', 'Parallel Computing'),
        ('BCS703', 'Cryptography & Network Security'),
        ('BCS714A', 'Deep Learning'),
        ('BCS714B', 'Natural Language Processing'),
        ('BAD714C', 'Social Network Analysis'),
        ('BCS714D', 'Big Data Analytics'),
        ('BCS755A', 'Introduction to DBMS'),
        ('BCS755B', 'Introduction to Algorithms'),
        ('BCS755C', 'Software Engineering'),
        ('BCS786', 'Major Project Phase-II')
    ]
    for code, name in cse_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE'], code, name, stream='computer_science')
    
    # AIML Subjects
    print("\n--- AIML Subjects ---")
    # 3rd Semester
    aiml_3rd = [
        ('BCS301', 'Mathematics for Computer Science'),
        ('BCS302', 'Digital Design & Computer Organization'),
        ('BCS303', 'Operating Systems'),
        ('BCS304', 'Data Structures and Applications'),
        ('BCSL305', 'Data Structures Lab'),
        ('BAI306A', 'Python for Artificial Intelligence'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BAIL358A', 'Data Analytics with Excel'),
        ('BAIL358B', 'R Programming'),
        ('BAIL358C', 'Data Visualization with Python'),
        ('BAIL358D', 'Project Management with Git')
    ]
    for code, name in aiml_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['AIML'], code, name, stream='computer_science')
    
    # 4th Semester
    aiml_4th = [
        ('BAI401', 'Analysis & Design of Algorithms'),
        ('BAI402', 'Machine Learning Foundations'),
        ('BCS403', 'Database Management Systems'),
        ('BAIL404', 'Machine Learning Lab'),
        ('BAI405A', 'Discrete Mathematical Structures'),
        ('BAI405B', 'Graph Theory'),
        ('BAI405C', 'Optimization Techniques'),
        ('BAI405D', 'Linear Algebra'),
        ('BAI456A', 'Green IT and Sustainability'),
        ('BAI456B', 'Capacity Planning for IT'),
        ('BAI456C', 'UI/UX'),
        ('BAIL456D', 'Technical Writing using LaTeX'),
        ('BBOC407', 'Biology for Computer Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in aiml_4th:
        add_subject(conn, scheme_id, semesters[4], branches['AIML'], code, name, stream='computer_science')
    
    # 5th Semester
    aiml_5th = [
        ('BCS501', 'Software Engineering & Project Management'),
        ('BAI502', 'Artificial Intelligence'),
        ('BCS503', 'Theory of Computation'),
        ('BAIL504', 'Data Visualization Lab'),
        ('BAI515A', 'Computer Vision'),
        ('BAI515B', 'Deep Learning'),
        ('BAI515C', 'Natural Language Processing'),
        ('BAI515D', 'Reinforcement Learning'),
        ('BAI586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BCS508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in aiml_5th:
        add_subject(conn, scheme_id, semesters[5], branches['AIML'], code, name, stream='computer_science')
    
    # 6th Semester
    aiml_6th = [
        ('BAI601', 'Advanced Machine Learning'),
        ('BAI602', 'Neural Networks and Deep Learning'),
        ('BAI613A', 'Generative AI'),
        ('BAI613B', 'Computer Vision'),
        ('BAI613C', 'Explainable AI'),
        ('BAI613D', 'Edge AI'),
        ('BCS654A', 'Introduction to Data Structures'),
        ('BCS654B', 'Fundamentals of Operating Systems'),
        ('BIS654C', 'Mobile Application Development'),
        ('BAI654D', 'Introduction to Artificial Intelligence'),
        ('BAI685', 'Project Phase-I'),
        ('BAIL606', 'Machine Learning Lab'),
        ('BAIL657A', 'Generative AI Lab'),
        ('BCSL657B', 'React'),
        ('BAIL657C', 'Prompt Engineering'),
        ('BCSL657D', 'DevOps'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in aiml_6th:
        add_subject(conn, scheme_id, semesters[6], branches['AIML'], code, name, stream='computer_science')
    
    # 7th Semester
    aiml_7th = [
        ('BAI701', 'Deep Learning'),
        ('BAI702', 'Large Language Models'),
        ('BAI703', 'AI Ethics and Governance'),
        ('BAI714A', 'Agentic AI'),
        ('BAI714B', 'MLOps'),
        ('BAI714C', 'Federated Learning'),
        ('BAI714D', 'Big Data Analytics'),
        ('BAI755A', 'Introduction to Machine Learning'),
        ('BAI755B', 'Introduction to Data Science'),
        ('BAI755C', 'Software Engineering'),
        ('BAI786', 'Major Project Phase-II')
    ]
    for code, name in aiml_7th:
        add_subject(conn, scheme_id, semesters[7], branches['AIML'], code, name, stream='computer_science')
    
    # CSE (Data Science) Subjects
    print("\n--- CSE (Data Science) Subjects ---")
    # 3rd Semester
    cseds_3rd = [
        ('BCS301', 'Mathematics for Computer Science'),
        ('BCS302', 'Digital Design & Computer Organization'),
        ('BCS303', 'Operating Systems'),
        ('BCS304', 'Data Structures and Applications'),
        ('BCSL305', 'Data Structures Lab'),
        ('BDS306A', 'Introduction to Data Science'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BDSL358A', 'Data Analytics with Excel'),
        ('BDSL358B', 'R Programming'),
        ('BDSL358C', 'Data Visualization with Python'),
        ('BDSL358D', 'SQL for Data Analytics')
    ]
    for code, name in cseds_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 4th Semester
    cseds_4th = [
        ('BCS401', 'Analysis & Design of Algorithms'),
        ('BDS402', 'Data Warehousing and Data Mining'),
        ('BCS403', 'Database Management Systems'),
        ('BCSL404', 'Analysis & Design of Algorithms Lab'),
        ('BDS405A', 'Discrete Mathematical Structures'),
        ('BDS405B', 'Graph Theory'),
        ('BDS405C', 'Optimization Techniques'),
        ('BDS405D', 'Linear Algebra'),
        ('BDS456A', 'Green IT and Sustainability'),
        ('BDS456B', 'Capacity Planning for IT'),
        ('BDS456C', 'UI/UX'),
        ('BDSL456D', 'Technical Writing using LaTeX'),
        ('BBOC407', 'Biology for Computer Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in cseds_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 5th Semester
    cseds_5th = [
        ('BCS501', 'Software Engineering & Project Management'),
        ('BDS502', 'Big Data Analytics'),
        ('BCS503', 'Theory of Computation'),
        ('BAIL504', 'Data Visualization Lab'),
        ('BDS515A', 'Data Mining'),
        ('BDS515B', 'Artificial Intelligence'),
        ('BDS515C', 'Cloud Computing'),
        ('BDS515D', 'Statistical Learning'),
        ('BDS586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BCS508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in cseds_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 6th Semester
    cseds_6th = [
        ('BAD601', 'Big Data Analytics'),
        ('BDS602', 'Artificial Intelligence & Machine Learning'),
        ('BDS613A', 'Deep Learning'),
        ('BDS613B', 'Data Engineering'),
        ('BDS613C', 'Natural Language Processing'),
        ('BDS613D', 'Time Series Analysis'),
        ('BCS654A', 'Introduction to Data Structures'),
        ('BCS654B', 'Fundamentals of Operating Systems'),
        ('BIS654C', 'Mobile Application Development'),
        ('BAI654D', 'Introduction to Artificial Intelligence'),
        ('BDS685', 'Project Phase-I'),
        ('BCSL606', 'Machine Learning Lab'),
        ('BDSL657A', 'Power BI and Business Analytics'),
        ('BCSL657B', 'React'),
        ('BAIL657C', 'Generative AI'),
        ('BCSL657D', 'DevOps'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in cseds_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 7th Semester
    cseds_7th = [
        ('BDS701', 'Parallel Programming'),
        ('BAD702', 'Statistical Machine Learning for Data Science'),
        ('BCS703', 'Cryptography & Network Security'),
        ('BDS714A', 'Advanced Data Analytics'),
        ('BDS714B', 'Data Science using Python'),
        ('BDS714C', 'Data Governance and Security'),
        ('BDS714D', 'Social Network Analysis'),
        ('BDS755A', 'Introduction to Data Analytics'),
        ('BDS755B', 'Introduction to Machine Learning'),
        ('BDS755C', 'Software Engineering'),
        ('BDS786', 'Major Project Phase-II')
    ]
    for code, name in cseds_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE_DS'], code, name, stream='computer_science')
    
    # CSE (Cyber Security) Subjects
    print("\n--- CSE (Cyber Security) Subjects ---")
    # 3rd Semester
    csecs_3rd = [
        ('BCS301', 'Mathematics for Computer Science'),
        ('BCS302', 'Digital Design & Computer Organization'),
        ('BCS303', 'Operating Systems'),
        ('BCS304', 'Data Structures and Applications'),
        ('BCSL305', 'Data Structures Lab'),
        ('BCY306A', 'Fundamentals of Cyber Security'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BCYL358A', 'Linux System Administration'),
        ('BCYL358B', 'Python for Cyber Security'),
        ('BCYL358C', 'Network Administration'),
        ('BCYL358D', 'Cyber Security Essentials')
    ]
    for code, name in csecs_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 4th Semester
    csecs_4th = [
        ('BCS401', 'Analysis & Design of Algorithms'),
        ('BCY402', 'Elements of Cyber Security'),
        ('BCS403', 'Database Management Systems'),
        ('BCSL404', 'Analysis & Design of Algorithms Lab'),
        ('BCY405A', 'Discrete Mathematical Structures'),
        ('BCY405B', 'Graph Theory'),
        ('BCY405C', 'Optimization Techniques'),
        ('BCY405D', 'Linear Algebra'),
        ('BCY456A', 'Green IT and Sustainability'),
        ('BCY456B', 'Capacity Planning for IT'),
        ('BCY456C', 'UI/UX'),
        ('BCYL456D', 'Technical Writing using LaTeX'),
        ('BBOC407', 'Biology for Computer Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in csecs_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 5th Semester
    csecs_5th = [
        ('BCS501', 'Software Engineering & Project Management'),
        ('BCS502', 'Computer Networks'),
        ('BCS503', 'Theory of Computation'),
        ('BCYL504', 'Advanced Cyber Security Lab'),
        ('BCY515A', 'Wireless and Mobile Device Security'),
        ('BCY515B', 'Ethical Hacking'),
        ('BCY515C', 'Digital Forensics'),
        ('BCY515D', 'Web Application Security'),
        ('BCY586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BCS508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in csecs_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 6th Semester
    csecs_6th = [
        ('BCO601', 'Microcontrollers & Embedded Systems'),
        ('BCY602', 'Cryptography & Network Security'),
        ('BCY613A', 'Blockchain Technology'),
        ('BCY613B', 'Cyber Threat Intelligence'),
        ('BCY613C', 'Cloud Security'),
        ('BCY613D', 'Malware Analysis'),
        ('BCS654A', 'Introduction to Data Structures'),
        ('BCS654B', 'Fundamentals of Operating Systems'),
        ('BIS654C', 'Mobile Application Development'),
        ('BAI654D', 'Introduction to Artificial Intelligence'),
        ('BCY685', 'Project Phase-I'),
        ('BCYL606', 'Network Security Lab'),
        ('BCYL657A', 'Industrial Cyber Security'),
        ('BCSL657B', 'React'),
        ('BAIL657C', 'Generative AI'),
        ('BCSL657D', 'DevOps'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in csecs_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 7th Semester
    csecs_7th = [
        ('BCY701', 'Vulnerability Assessment & Penetration Testing'),
        ('BCY702', 'Ethical Hacking'),
        ('BIC703', 'Machine Learning'),
        ('BCY714A', 'Introduction to Cyber Forensics'),
        ('BCY714B', 'Software Defined Networks'),
        ('BCY714C', 'Cyber Policies and CERT-IN'),
        ('BCY714D', 'Cyber Security Management, Compliance and Governance'),
        ('BCY755A', 'Introduction to Cyber Security'),
        ('BCY755B', 'Information Security'),
        ('BCY755C', 'Network Security'),
        ('BCY786', 'Major Project Phase-II')
    ]
    for code, name in csecs_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE_CS'], code, name, stream='computer_science')
    
    # ECE Subjects
    print("\n--- ECE Subjects ---")
    # 3rd Semester
    ece_3rd = [
        ('BMATEC301', 'AV Mathematics-III for EC Engineering'),
        ('BEC302', 'Digital System Design using Verilog'),
        ('BEC303', 'Electronic Principles and Circuits'),
        ('BEC304', 'Network Analysis'),
        ('BECL305', 'Analog and Digital Systems Design Lab'),
        ('BEC306A', 'Electronic Devices'),
        ('BEC306B', 'Sensors and Instrumentation'),
        ('BEC306C', 'Computer Organization and Architecture'),
        ('BEC306D', 'Applied Numerical Methods for EC Engineers'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BEC358A', 'LABVIEW Programming'),
        ('BEC358B', 'MATLAB Programming'),
        ('BEC358C', 'C++ Basics'),
        ('BEC358D', 'IoT for Smart Infrastructure')
    ]
    for code, name in ece_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['ECE'], code, name, stream='electronics')
    
    # 4th Semester
    ece_4th = [
        ('BEC401', 'Electromagnetic Theory'),
        ('BEC402', 'Principles of Communication Systems'),
        ('BEC403', 'Control Systems'),
        ('BECL404', 'Communication Lab'),
        ('BEC405A', 'Analog IC Design'),
        ('BEC405B', 'Embedded C Programming'),
        ('BEC405C', 'Signals and Systems'),
        ('BEC405D', 'Digital Signal Processing Fundamentals'),
        ('BEC456A', 'PCB Design Lab'),
        ('BEC456B', 'Microcontroller Applications Lab'),
        ('BEC456C', 'Sensor Interfacing Lab'),
        ('BEC456D', 'IoT Applications Lab'),
        ('BBOC407', 'Biology for Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in ece_4th:
        add_subject(conn, scheme_id, semesters[4], branches['ECE'], code, name, stream='electronics')
    
    # 5th Semester
    ece_5th = [
        ('BEC501', 'Technological Innovation and Management Entrepreneurship'),
        ('BEC502', 'Digital Signal Processing'),
        ('BEC503', 'Digital Communication'),
        ('BECL504', 'Digital Communication Lab'),
        ('BEC515A', 'Intelligent Systems and Machine Learning Algorithms'),
        ('BEC515B', 'Digital Image Processing'),
        ('BEC515C', 'Computer and Data Security'),
        ('BEC515D', 'FPGA System Design using Verilog'),
        ('BEC586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BESK508', 'Environmental Studies')
    ]
    for code, name in ece_5th:
        add_subject(conn, scheme_id, semesters[5], branches['ECE'], code, name, stream='electronics')
    
    # 6th Semester
    ece_6th = [
        ('BEC601', 'Embedded System Design'),
        ('BEC602', 'VLSI Design and Testing'),
        ('BEC613A', 'Cyber Security'),
        ('BEC613B', 'Automotive Electronics'),
        ('BEC613C', 'Radar Communication'),
        ('BEC613D', 'Internet of Things'),
        ('BEC654A', 'Digital System Design using Verilog'),
        ('BEC654B', 'Consumer Electronics'),
        ('BEC654C', 'Electronic Communication Systems'),
        ('BEC654D', 'Basic VLSI Design'),
        ('BEC685', 'Project Phase-I'),
        ('BECL606', 'VLSI Design and Testing Lab'),
        ('BEC657A', 'Embedded Systems Laboratory'),
        ('BEC657B', 'FPGA Applications Lab'),
        ('BEC657C', 'IoT Laboratory'),
        ('BEC657D', 'Machine Learning Applications Lab'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in ece_6th:
        add_subject(conn, scheme_id, semesters[6], branches['ECE'], code, name, stream='electronics')
    
    # 7th Semester
    ece_7th = [
        ('BEC701', 'Microwave Engineering and Antenna Theory'),
        ('BEC702', 'Computer Networks and Protocols'),
        ('BEC703', 'Wireless Communication Systems'),
        ('BEC714A', 'Artificial Intelligence for Communication Systems'),
        ('BEC714B', 'Advanced VLSI Design'),
        ('BEC714C', 'Advanced Embedded Systems'),
        ('BEC714D', 'Optical Communication Networks'),
        ('BEC755A', 'Sensors and Actuators'),
        ('BEC755B', 'Consumer Electronics'),
        ('BEC755C', 'Electronic Product Design'),
        ('BEC755D', 'Communication Network Security'),
        ('BEC786', 'Major Project Phase-II')
    ]
    for code, name in ece_7th:
        add_subject(conn, scheme_id, semesters[7], branches['ECE'], code, name, stream='electronics')
    
    # Mechanical Subjects
    print("\n--- Mechanical Subjects ---")
    # 3rd Semester
    me_3rd = [
        ('BMATM301', 'Mathematics for Mechanical Engineering'),
        ('BME302', 'Material Science and Metallurgy'),
        ('BME303', 'Basic Thermodynamics'),
        ('BME304', 'Manufacturing Process'),
        ('BME305', 'Engineering Mechanics'),
        ('BMEL306', 'Manufacturing Process Laboratory'),
        ('BME307A', 'Computer Aided Engineering Drawing'),
        ('BME307B', 'Engineering Graphics Applications'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BMEL358A', 'MATLAB for Mechanical Engineering'),
        ('BMEL358B', 'CAD Modelling Laboratory'),
        ('BMEL358C', 'Python Programming for Engineers'),
        ('BMEL358D', 'Spreadsheet Applications for Engineers')
    ]
    for code, name in me_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['ME'], code, name, stream='mechanical')
    
    # 4th Semester
    me_4th = [
        ('BMATM401', 'Mathematics for Mechanical Engineering-IV'),
        ('BME402', 'Applied Thermodynamics'),
        ('BME403', 'Fluid Mechanics'),
        ('BME404', 'Kinematics of Machines'),
        ('BMEL405', 'Fluid Mechanics and Machinery Lab'),
        ('BME405A', 'Machine Drawing'),
        ('BME405B', 'Industrial Engineering'),
        ('BME405C', 'Engineering Materials'),
        ('BME405D', 'Mechatronics Fundamentals'),
        ('BMEL456A', 'Simulation of Mechanical Systems'),
        ('BMEL456B', 'PLC Applications Lab'),
        ('BMEL456C', 'Surface Modelling Lab'),
        ('BMEL456D', 'Machine Learning using Python'),
        ('BBOC407', 'Biology for Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in me_4th:
        add_subject(conn, scheme_id, semesters[4], branches['ME'], code, name, stream='mechanical')
    
    # 5th Semester
    me_5th = [
        ('BME501', 'Engineering Management and Entrepreneurship'),
        ('BME502', 'Heat Transfer'),
        ('BME503', 'Dynamics of Machines'),
        ('BME504', 'Design of Machine Elements-I'),
        ('BME515A', 'Mechatronics'),
        ('BME515B', 'Energy Conversion Engineering'),
        ('BME515C', 'Supply Chain Management'),
        ('BME515D', 'Production Planning and Control'),
        ('BMEL505', 'Heat Transfer Laboratory'),
        ('BME586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BME508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in me_5th:
        add_subject(conn, scheme_id, semesters[5], branches['ME'], code, name, stream='mechanical')
    
    # 6th Semester
    me_6th = [
        ('BME601', 'Design of Machine Elements-II'),
        ('BME602', 'Computer Integrated Manufacturing'),
        ('BME603', 'Hydraulics and Pneumatics'),
        ('BME604', 'Operations Research'),
        ('BME613A', 'Turbo Machines'),
        ('BME613B', 'Additive Manufacturing'),
        ('BME613C', 'Automobile Engineering and Electric Vehicles'),
        ('BME613D', 'Theory of Elasticity'),
        ('BME654A', 'Fundamentals of Robotics'),
        ('BME654B', 'Project Management'),
        ('BME654C', 'Industrial Automation'),
        ('BME654D', 'Renewable Energy Engineering'),
        ('BMEL606', 'CNC and CAD/CAM Laboratory'),
        ('BME685', 'Project Phase-I'),
        ('BMEL657A', 'Electric Vehicle Technology'),
        ('BMEL657B', 'Enterprise Systems'),
        ('BMEL657C', 'Microcontrollers and Control Systems'),
        ('BMEL657D', '3D Printing Laboratory'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in me_6th:
        add_subject(conn, scheme_id, semesters[6], branches['ME'], code, name, stream='mechanical')
    
    # 7th Semester
    me_7th = [
        ('BME701', 'Finite Element Methods'),
        ('BME702', 'Refrigeration and Air Conditioning'),
        ('BME703', 'Robotics and Automation'),
        ('BME714A', 'Smart Materials and Systems'),
        ('BME714B', 'Industry 4.0'),
        ('BME714C', 'Composite Materials'),
        ('BME714D', 'Non-Traditional Machining Processes'),
        ('BME755A', 'Quantitative Techniques for Decision Making'),
        ('BME755B', 'Total Quality Management'),
        ('BME755C', 'Industrial Safety Engineering'),
        ('BME755D', 'Energy Management'),
        ('BME786', 'Major Project Phase-II')
    ]
    for code, name in me_7th:
        add_subject(conn, scheme_id, semesters[7], branches['ME'], code, name, stream='mechanical')
    
    # EEE Subjects
    print("\n--- EEE Subjects ---")
    # 3rd Semester
    eee_3rd = [
        ('BEE301', 'Engineering Mathematics for EEE'),
        ('BEE302', 'Electric Circuit Analysis'),
        ('BEE303', 'Analog Electronic Circuits'),
        ('BEE304', 'Transformers and Generators'),
        ('BEEL305', 'Transformers and Generators Lab'),
        ('BEE306A', 'Digital Logic Circuits'),
        ('BEE306B', 'Electrical Measurements and Instrumentation'),
        ('BEE306C', 'Electromagnetic Field Theory'),
        ('BEE306D', 'Physics of Electronic Devices'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BEEL358A', 'SCI/MATLAB for Transformers and Generators'),
        ('BEEL358B', '555 IC Laboratory'),
        ('BEEL358C', 'Circuit Laboratory using PSPICE'),
        ('BEEL358D', 'Electrical Hardware Laboratory')
    ]
    for code, name in eee_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['EEE'], code, name, stream='electrical')
    
    # 4th Semester
    eee_4th = [
        ('BEE401', 'Electric Motors'),
        ('BEE402', 'Transmission and Distribution'),
        ('BEE403', 'Microcontrollers'),
        ('BEEL404', 'Electric Motors Lab'),
        ('BEE405A', 'Electrical Power Generation and Economics'),
        ('BEE405B', 'Operational Amplifiers and Linear ICs'),
        ('BEE405C', 'Engineering Materials'),
        ('BEE405D', 'Object Oriented Programming'),
        ('BEEL456A', 'Basics of VHDL Lab'),
        ('BEEL456B', 'MATLAB for Measurements Lab'),
        ('BEEL456C', 'PCB Design Laboratory'),
        ('BEEL456D', 'Arduino & Raspberry Pi Based Projects'),
        ('BBOC407', 'Biology for Engineers'),
        ('BUHK408', 'Universal Human Values')
    ]
    for code, name in eee_4th:
        add_subject(conn, scheme_id, semesters[4], branches['EEE'], code, name, stream='electrical')
    
    # 5th Semester
    eee_5th = [
        ('BEE501', 'Engineering Management and Entrepreneurship'),
        ('BEE502', 'Signals & DSP'),
        ('BEE503', 'Power Electronics'),
        ('BEEL504', 'Power Electronics Lab'),
        ('BEE515A', 'High Voltage Engineering'),
        ('BEE515B', 'Power Electronics for Renewable Energy Systems'),
        ('BEE515C', 'Electric Vehicle Fundamentals'),
        ('BEE515D', 'Fundamentals of VLSI Design'),
        ('BEE586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BEE508', 'Environmental Studies and E-Waste Management')
    ]
    for code, name in eee_5th:
        add_subject(conn, scheme_id, semesters[5], branches['EEE'], code, name, stream='electrical')
    
    # 6th Semester
    eee_6th = [
        ('BEE601', 'Power System Analysis-I'),
        ('BEE602', 'Control Systems'),
        ('BEE613A', 'Medium Voltage Substation Design'),
        ('BEE613B', 'Embedded System Design'),
        ('BEE613C', 'FACTS and HVDC Transmission'),
        ('BEE613D', 'Electric Motor and Drive Systems for EVs'),
        ('BEE654A', 'Utilization of Electrical Power'),
        ('BEE654B', 'Technologies of Renewable Energy Sources'),
        ('BEE654C', 'Industrial Servo Control Systems'),
        ('BEE654D', 'Semiconductor Devices'),
        ('BEE685', 'Project Phase-I'),
        ('BEEL606', 'Control Systems Lab'),
        ('BEE657A', 'Energy Management in Electric Vehicles'),
        ('BEEL657B', 'Simulation of Power Electronic Circuits'),
        ('BEEL657C', 'Energy Audit Project'),
        ('BEEL657D', 'Renewable Energy Systems Project'),
        ('BIKS609', 'Indian Knowledge System')
    ]
    for code, name in eee_6th:
        add_subject(conn, scheme_id, semesters[6], branches['EEE'], code, name, stream='electrical')
    
    # 7th Semester
    eee_7th = [
        ('BEE701', 'Switchgear and Protection'),
        ('BEE702', 'Industrial Drives and Applications'),
        ('BEE703', 'Power System Analysis-II'),
        ('BEE714A', 'Power System Operation and Control'),
        ('BEE714B', 'AI Techniques for Electric and Hybrid Vehicles'),
        ('BEE714C', 'Programmable Logic Controllers'),
        ('BEE714D', 'Big Data Analytics in Power Systems'),
        ('BEE755A', 'Electric Vehicle Technologies'),
        ('BEE755B', 'Energy Conservation and Audit'),
        ('BEE755C', 'PLC and SCADA'),
        ('BEE755D', 'Optimization Techniques'),
        ('BEE786', 'Major Project Phase-II')
    ]
    for code, name in eee_7th:
        add_subject(conn, scheme_id, semesters[7], branches['EEE'], code, name, stream='electrical')
    
    if conn is None:
        conn.close()

def main():
    conn = init_connection()
    populate(conn)
    conn.close()
    print("\n✅ 2022 Scheme populated!")

if __name__ == "__main__":
    main()
