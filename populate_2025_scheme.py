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
    cursor.execute("""
        SELECT id FROM subjects 
        WHERE scheme_id = ? AND semester_id = ? AND branch_id = ? AND code = ?
    """, (scheme_id, semester_id, branch_id, code))
    row = cursor.fetchone()
    if row:
        print(f"Subject {code} - {name} already exists")
        return row['id']
    
    cursor.execute("""
        INSERT INTO subjects 
        (scheme_id, semester_id, branch_id, name, code, stream, is_common) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (scheme_id, semester_id, branch_id, name, code, stream, is_common))
    conn.commit()
    print(f"Added subject: {code} - {name}")
    return cursor.lastrowid

def populate(conn=None):
    if conn is None:
        conn = init_connection()
    
    # Create 2025 scheme
    scheme_id = get_or_create_scheme(conn, '2025 Scheme', 'VTU 2025 Scheme for Engineering')
    
    # Get semesters 1-7 for 2025 scheme
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
    
    # ==================== CSE Subjects ====================
    print("\n--- 2025 CSE Subjects ---")
    
    # 3rd Semester
    cse_3rd = [
        ('1BCS301', 'Probability, Distributions and Statistics'),
        ('1BCS302', 'Object Oriented Programming with Java'),
        ('1BCS303', 'Digital Design and Computer Organization'),
        ('1BCS304', 'Operating Systems'),
        ('1BCS305', 'Data Structures and Applications'),
        ('1BCSL306', 'Data Structures Laboratory'),
        ('1BCSL307A', 'Project Management (with Git)'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in cse_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE'], code, name, stream='computer_science')
    
    # 4th Semester
    cse_4th = [
        ('1BCS401', 'Discrete Mathematics and Graph Theory'),
        ('1BCE402', 'Microcontrollers'),
        ('1BCS403', 'Computer Networks'),
        ('1BCS404', 'Design and Analysis of Algorithms'),
        ('1BCSL405', 'Algorithms Laboratory'),
        ('1BCGL406A', 'Web Application Development'),
        ('1BCGL406B', 'UI/UX'),
        ('1BCS407', 'Biology for Computer Engineers'),
        ('1BEP408', 'Environmental Science Project')
    ]
    for code, name in cse_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE'], code, name, stream='computer_science')
    
    # 5th Semester
    cse_5th = [
        ('1BCS501', 'Software Engineering and Project Management'),
        ('1BCM502', 'Database Management Systems'),
        ('1BCS503', 'Theory of Computation'),
        ('1BCE504', 'Machine Learning'),
        ('1BCS505A', 'Digital Image Processing'),
        ('1BCE505B', 'Cloud Computing'),
        ('1BCG505C', 'Computer Graphics'),
        ('1BCE505D', 'Unix System Programming'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BCEL507', 'Machine Learning Laboratory'),
        ('1BCE508', 'Hackathon-Based Project')
    ]
    for code, name in cse_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE'], code, name, stream='computer_science')
    
    # 6th Semester
    cse_6th = [
        ('1BCS601', 'Advanced Java Programming'),
        ('1BCS602', 'Cryptography and Network Security'),
        ('1BCE603', 'Advanced Computer Architecture'),
        ('1BCS604', 'Internet of Things'),
        ('1BCB605A', 'Artificial Intelligence'),
        ('1BCG605B', 'Robotic Process Automation with UiPath'),
        ('1BCE605C', 'Compiler Design'),
        ('1BCG605D', 'Designing Distributed Systems'),
        ('1BCSL606', 'IoT Laboratory'),
        ('1BCGL607A', 'Progressive Web Application Development with Flutter'),
        ('1BAIL607B', 'Generative AI'),
        ('1BCGL607C', 'Mobile First Web Design with W3.CSS'),
        ('1BCGL607D', 'Data Visualization'),
        ('1BCE608', 'Capstone Project Phase-I'),
        ('1BXX609', 'Universal Human Value')
    ]
    for code, name in cse_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE'], code, name, stream='computer_science')
    
    # 7th Semester
    cse_7th = [
        ('1BIS701', 'High Performance Computing'),
        ('1BCS702A', 'Deep Learning'),
        ('1BCG702B', 'Big Data Analytics'),
        ('1BCG702C', 'Embedded Systems Design'),
        ('1BCB702D', 'IoT Analytics'),
        ('1BCS703A', 'Agentic Artificial Intelligence'),
        ('1BDS703B', 'Social Network Analysis'),
        ('1BCG703C', 'Blockchain Technology'),
        ('1BCN703D', 'Quantum Computing'),
        ('1BCS704A', 'Introduction to Data Structures'),
        ('1BIS704B', 'Java Programming'),
        ('1BCE704C', 'Introduction to Quantum Computing'),
        ('1BXX704D', 'Foreign Language'),
        ('1BCE705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in cse_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE'], code, name, stream='computer_science')
    
    # ==================== AIML Subjects ====================
    print("\n--- 2025 AIML Subjects ---")
    
    # 3rd Semester
    aiml_3rd = [
        ('1BCS301', 'Probability, Distributions and Statistics'),
        ('1BCS302', 'Object Oriented Programming with Java'),
        ('1BCS303', 'Digital Design and Computer Organization'),
        ('1BCS304', 'Operating Systems'),
        ('1BCS305', 'Data Structures and Applications'),
        ('1BCSL306', 'Data Structures Laboratory'),
        ('1BAIL307A', 'Exploratory Data Analysis'),
        ('1BCSL307A', 'Project Management (with Git)'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in aiml_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['AIML'], code, name, stream='computer_science')
    
    # 4th Semester
    aiml_4th = [
        ('1BAI401', 'Discrete Mathematics and Optimization Techniques'),
        ('1BAI402', 'Design and Analysis of Algorithms'),
        ('1BAI403', 'Database Management Systems'),
        ('1BAI404', 'Machine Learning'),
        ('1BAIL405', 'Machine Learning Laboratory'),
        ('1BCIL406A', 'Mobile Application Development'),
        ('1BCGL406A', 'Web Application Development'),
        ('1BCGL406B', 'UI/UX'),
        ('1BADL406A', 'Unix Shell Programming'),
        ('1BCS407', 'Biology for Computer Engineers'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BMUS409', 'Music')
    ]
    for code, name in aiml_4th:
        add_subject(conn, scheme_id, semesters[4], branches['AIML'], code, name, stream='computer_science')
    
    # 5th Semester
    aiml_5th = [
        ('1BCS501', 'Software Engineering and Project Management'),
        ('1BAI502', 'Artificial Intelligence'),
        ('1BCS503', 'Theory of Computation'),
        ('1BAI504', 'Computer Networks'),
        ('1BAI505B', 'Image and Video Processing'),
        ('1BCE505B', 'Cloud Computing'),
        ('1BCR505B', 'Soft Computing'),
        ('1BCS505C', 'Natural Language Processing'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BAIL507', 'Data Visualization Laboratory'),
        ('1BCI508', 'Hackathon-Based Project')
    ]
    for code, name in aiml_5th:
        add_subject(conn, scheme_id, semesters[5], branches['AIML'], code, name, stream='computer_science')
    
    # 6th Semester
    aiml_6th = [
        ('1BCS601', 'Advanced Java Programming'),
        ('1BIS602', 'Information and Network Security'),
        ('1BCI603', 'High Performance Computing in Artificial Intelligence'),
        ('1BCS604', 'Internet of Things'),
        ('1BAI605A', 'Artificial Superintelligence'),
        ('1BAD605A', 'Prompt Engineering'),
        ('1BCI605C', 'Generative AI'),
        ('1BCI605D', 'AI Ethics and Sustainability'),
        ('1BCSL606', 'IoT Laboratory'),
        ('1BCAL607C', 'MongoDB'),
        ('1BCSL607C', 'DevOps'),
        ('1BADL607B', 'Object Oriented Modeling using UML'),
        ('1BCSL607A', 'Full Stack Development'),
        ('1BCI608', 'Capstone Project Phase-I'),
        ('1BXX609', 'Universal Human Value')
    ]
    for code, name in aiml_6th:
        add_subject(conn, scheme_id, semesters[6], branches['AIML'], code, name, stream='computer_science')
    
    # 7th Semester
    aiml_7th = [
        ('1BCD701', 'Deep Learning'),
        ('1BCI702A', 'Data Engineering & MLOps'),
        ('1BCG702B', 'Big Data Analytics'),
        ('1BAD702A', 'Feature Engineering'),
        ('1BAD702C', 'Edge AI & Federated Learning'),
        ('1BCS703A', 'Agentic Artificial Intelligence'),
        ('1BCN703A', 'Quantum Computing'),
        ('1BCG703C', 'Blockchain Technology'),
        ('1BDS703B', 'Social Network Analysis'),
        ('1BAI704C', 'Introduction to Machine Learning'),
        ('1BCS704B', 'Introduction to Algorithms'),
        ('1BIS704C', 'Introduction to Information Security'),
        ('1BXX704D', 'Foreign Language'),
        ('1BCI705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in aiml_7th:
        add_subject(conn, scheme_id, semesters[7], branches['AIML'], code, name, stream='computer_science')
    
    # ==================== CSE (Cyber Security) Subjects ====================
    print("\n--- 2025 CSE (Cyber Security) Subjects ---")
    
    # 3rd Semester
    cs_3rd = [
        ('1BCS301', 'Probability, Distributions and Statistics'),
        ('1BCS302', 'Object Oriented Programming with Java'),
        ('1BCS303', 'Digital Design and Computer Organization'),
        ('1BCS304', 'Operating Systems'),
        ('1BCS305', 'Data Structures and Applications'),
        ('1BCSL306', 'Data Structures Laboratory'),
        ('1BCSL307A', 'Project Management (with Git)'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in cs_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 4th Semester
    cs_4th = [
        ('1BAI401', 'Discrete Mathematics and Optimization Techniques'),
        ('1BAI402', 'Design and Analysis of Algorithms'),
        ('1BAI403', 'Database Management Systems'),
        ('1BCY404', 'Elements of Cyber Security'),
        ('1BCYL405', 'Cyber Security Laboratory'),
        ('1BCYL406A', 'Rust for Cyber Security'),
        ('1BCYL406B', 'Malware Analysis'),
        ('1BCS407', 'Biology for Computer Engineers'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BMUS409', 'Music')
    ]
    for code, name in cs_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 5th Semester
    cs_5th = [
        ('1BCS501', 'Software Engineering and Project Management'),
        ('1BCS502', 'Machine Learning'),
        ('1BCS503', 'Theory of Computation'),
        ('1BAI504', 'Computer Networks'),
        ('1BIC505A', 'Wireless and Mobile Device Security'),
        ('1BCY505B', 'API Security'),
        ('1BCY505C', 'Incident Management in Cyber Security'),
        ('1BCY505D', 'Security for Web Developers'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BCYL507', 'Ethical Hacking Laboratory'),
        ('1BCY508', 'Hackathon-Based Project')
    ]
    for code, name in cs_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 6th Semester
    cs_6th = [
        ('1BIC601', 'Blockchain Technology'),
        ('1BCS602', 'Cryptography and Network Security'),
        ('1BCY603', 'Database Security'),
        ('1BCY604', 'Cloud Computing and Security'),
        ('1BCY605A', 'Malware Data Science'),
        ('1BIC605B', 'Standards and Best Practices – CIS, NIST, CISA'),
        ('1BCY605C', 'Digital Forensics'),
        ('1BCY605D', 'Problem Management in Cyber Security'),
        ('1BCYL606', 'Cryptography and Network Security Laboratory'),
        ('1BCYL607A', 'Industrial Cyber Security'),
        ('1BAIL607B', 'Generative AI'),
        ('1BCYL607C', 'Mobile Phone Forensics'),
        ('1BCGL607D', 'Data Visualization'),
        ('1BCY608', 'Capstone Project Phase-I'),
        ('1BXX609', 'Universal Human Value')
    ]
    for code, name in cs_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE_CS'], code, name, stream='computer_science')
    
    # 7th Semester
    cs_7th = [
        ('1BCY701', 'Vulnerability Assessment and Penetration Testing'),
        ('1BCS702A', 'Deep Learning'),
        ('1BCY702B', 'DApps and Smart Contracts for Blockchain'),
        ('1BCY702C', 'Cyber Policies and CERT-IN'),
        ('1BCY702D', 'Cyber Security Management, Compliance and Governance'),
        ('1BCY703A', 'Managed Detection and Response (MDR)'),
        ('1BIC703B', 'IoT and OT Security'),
        ('1BCY703C', 'Cyber Analytics'),
        ('1BCY703D', 'Social Media Security'),
        ('1BCS704A', 'Introduction to Data Structures'),
        ('1BAI704B', 'Introduction to Cloud Computing'),
        ('1BCY704C', 'Introduction to Cyber Security'),
        ('1BXX704D', 'Foreign Language'),
        ('1BCY705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in cs_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE_CS'], code, name, stream='computer_science')
    
    # ==================== CSE (Data Science) Subjects ====================
    print("\n--- 2025 CSE (Data Science) Subjects ---")
    
    # 3rd Semester
    ds_3rd = [
        ('1BCS301', 'Probability, Distributions and Statistics'),
        ('1BCS302', 'Object Oriented Programming with Java'),
        ('1BCS303', 'Digital Design and Computer Organization'),
        ('1BCS304', 'Operating Systems'),
        ('1BCS305', 'Data Structures and Applications'),
        ('1BCSL306', 'Data Structures Laboratory'),
        ('1BAIL307A', 'Exploratory Data Analysis'),
        ('1BCSL307A', 'Project Management (with Git)'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in ds_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 4th Semester
    ds_4th = [
        ('1BAI401', 'Discrete Mathematics and Optimization Techniques'),
        ('1BAI402', 'Design and Analysis of Algorithms'),
        ('1BAI403', 'Database Management Systems'),
        ('1BAI404', 'Machine Learning'),
        ('1BAIL405', 'Machine Learning Laboratory'),
        ('1BCDL406A', 'Cloud Data Warehouse Implementation Using Snowflake'),
        ('1BCDL406B', 'JULIA Programming'),
        ('1BCDL406C', 'MERN Stack Development'),
        ('1BCS407', 'Biology for Computer Engineers'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BMUS409', 'Music')
    ]
    for code, name in ds_4th:
        add_subject(conn, scheme_id, semesters[4], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 5th Semester
    ds_5th = [
        ('1BCS501', 'Software Engineering and Project Management'),
        ('1BDS502', 'NoSQL Databases'),
        ('1BCS503', 'Theory of Computation'),
        ('1BAI504', 'Computer Networks'),
        ('1BIS505A', 'Digital Image Processing'),
        ('1BCE505B', 'Cloud Computing'),
        ('1BIS505B', 'Artificial Intelligence'),
        ('1BAD505D', 'Mining Massive Data'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BAIL507', 'Data Visualization Laboratory'),
        ('1BCD508', 'Hackathon-Based Project')
    ]
    for code, name in ds_5th:
        add_subject(conn, scheme_id, semesters[5], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 6th Semester
    ds_6th = [
        ('1BCS601', 'Advanced Java Programming'),
        ('1BAD602', 'Data Security and Privacy'),
        ('1BCS603', 'High Performance Computing'),
        ('1BAD604', 'Big Data Analytics'),
        ('1BCG605B', 'Robotic Process Automation with UiPath'),
        ('1BAD605A', 'Prompt Engineering'),
        ('1BAD605C', 'Internet of Things'),
        ('1BCD605D', 'Time Series Analysis'),
        ('1BDSL606', 'Big Data Analytics Laboratory'),
        ('1BCGL607A', 'Progressive Web Application Development with Flutter'),
        ('1BCSL607C', 'DevOps'),
        ('1BADL607C', 'Front End Web Development using ReactJS'),
        ('1BAIL607B', 'Generative AI'),
        ('1BCD608', 'Capstone Project Phase-I'),
        ('1BXX609', 'Universal Human Value')
    ]
    for code, name in ds_6th:
        add_subject(conn, scheme_id, semesters[6], branches['CSE_DS'], code, name, stream='computer_science')
    
    # 7th Semester
    ds_7th = [
        ('1BCD701', 'Data Engineering'),
        ('1BAD702A', 'Advanced Data Analytics'),
        ('1BCD702B', 'Data Warehousing and Business Intelligence'),
        ('1BCD702C', 'Predictive Analytics'),
        ('1BCD702D', 'Social Network Analysis'),
        ('1BCD703A', 'Data Governance and Security'),
        ('1BCD703B', 'MLOps'),
        ('1BCD703C', 'Big Data Technologies'),
        ('1BCD703D', 'Deep Learning for Data Science'),
        ('1BDS704A', 'Introduction to Data Analytics'),
        ('1BAI704B', 'Introduction to Machine Learning'),
        ('1BCS704C', 'Database Systems'),
        ('1BXX704D', 'Foreign Language'),
        ('1BCD705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in ds_7th:
        add_subject(conn, scheme_id, semesters[7], branches['CSE_DS'], code, name, stream='computer_science')
    
    # ==================== ME Subjects ====================
    print("\n--- 2025 ME Subjects ---")
    
    # 3rd Semester
    me_3rd = [
        ('1BMATM301', 'Program Specific Mathematics'),
        ('1BME302', 'Material Science and Metallurgy'),
        ('1BME303', 'Basic Thermodynamics'),
        ('1BME304', 'Mechanics of Materials'),
        ('1BME305', 'Manufacturing Technology - I'),
        ('1BMEL306', 'Computer Aided Machine Drawing Lab'),
        ('1BMEL307A', 'MATLAB for Engineering Computation'),
        ('1BMEL307B', 'Virtual Reality'),
        ('1BMEL307C', 'Spreadsheet for Engineers'),
        ('1BME307D', 'AI & Prompt Engineering'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in me_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['ME'], code, name, stream='mechanical')
    
    # 4th Semester
    me_4th = [
        ('1BMATM401', 'Programme Specific Mathematics'),
        ('1BME402', 'Manufacturing Technology - II'),
        ('1BME403', 'Applied Thermodynamics'),
        ('1BME404', 'Fluid Mechanics & Machinery'),
        ('1BMEL405', 'Mechanical Measurements and Metrology Lab'),
        ('1BMEL406A', 'Machine Learning using Python'),
        ('1BMEL406B', 'PLC and Automation'),
        ('1BMEL406C', 'Simulation of Kinematic Systems'),
        ('1BMEL406D', 'Surface Modelling'),
        ('1BME407', 'Biology for Engineers'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BME409', 'Kinematics of Machines'),
        ('1BMUS409', 'Music')
    ]
    for code, name in me_4th:
        add_subject(conn, scheme_id, semesters[4], branches['ME'], code, name, stream='mechanical')
    
    # 5th Semester
    me_5th = [
        ('1BME501', 'Management and Engineering Economics'),
        ('1BME502', 'Heat Transfer'),
        ('1BME503', 'Control Engineering'),
        ('1BME504', 'Dynamics of Machines'),
        ('1BME505A', 'Mechatronics'),
        ('1BME505B', 'Energy Conversion Technology'),
        ('1BME505C', 'Supply Chain Management'),
        ('1BME505D', 'Production Planning and Control'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BMEL507', 'Thermo-fluids Lab'),
        ('1BME508', 'Hackathon-Based Project')
    ]
    for code, name in me_5th:
        add_subject(conn, scheme_id, semesters[5], branches['ME'], code, name, stream='mechanical')
    
    # 6th Semester
    me_6th = [
        ('1BME601', 'Hydraulics and Pneumatics'),
        ('1BME602', 'Machine Design'),
        ('1BME603', 'Computer Integrated Manufacturing'),
        ('1BME604', 'Operations Research'),
        ('1BME605A', 'Turbo Machines'),
        ('1BME605B', 'Additive Manufacturing'),
        ('1BME605C', 'Automobile Engineering and Electric Vehicle'),
        ('1BME605D', 'Theory of Elasticity'),
        ('1BMEL606', 'CNC Lab'),
        ('1BMEL607A', 'Microcontrollers and Interfacing of Control Systems'),
        ('1BMEL607B', 'Enterprise Systems'),
        ('1BMEL607C', 'Electric Vehicle Technology'),
        ('1BMEL607D', '3D Printing'),
        ('1BME608', 'Capstone Project Phase-I'),
        ('1BME609', 'Universal Human Values')
    ]
    for code, name in me_6th:
        add_subject(conn, scheme_id, semesters[6], branches['ME'], code, name, stream='mechanical')
    
    # 7th Semester
    me_7th = [
        ('1BME701', 'Finite Element Methods'),
        ('1BME702A', 'Smart Materials and Systems'),
        ('1BME702B', 'Refrigeration & Air Conditioning'),
        ('1BME702C', 'Robotics and Automation'),
        ('1BME702D', 'Non-traditional Machining Processes'),
        ('1BME703A', 'Total Quality Management'),
        ('1BME703B', 'Industry 5.0'),
        ('1BME703C', 'Composite Materials'),
        ('1BME703D', 'Theory of Plasticity'),
        ('1BME704A', 'Quantitative Techniques for Decision Making'),
        ('1BME704B', 'Project Management'),
        ('1BME704C', 'Fundamentals of Robotics'),
        ('1BME704D', 'Foreign Language'),
        ('1BME705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in me_7th:
        add_subject(conn, scheme_id, semesters[7], branches['ME'], code, name, stream='mechanical')
    
    # ==================== EEE Subjects ====================
    print("\n--- 2025 EEE Subjects ---")
    
    # 3rd Semester
    eee_3rd = [
        ('1BMAT301', 'Mathematics III for EEE'),
        ('1BEE302', 'Analog Electronics Circuits'),
        ('1BEE303', 'Electric Circuit Analysis'),
        ('1BEE304', 'Digital Electronics Circuits'),
        ('1BEE305', 'Transformers and Generators'),
        ('1BEEL306', 'Transformers and Generators Lab'),
        ('1BEEL307A', 'Multisim/PSPICE Lab for Circuit Analysis'),
        ('1BEEL307B', 'Transducers and Sensors Lab'),
        ('1BEE307C', 'Python Programming'),
        ('1BEE307D', 'Digital Electronics Circuits Lab'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in eee_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['EEE'], code, name, stream='electrical')
    
    # 4th Semester
    eee_4th = [
        ('1BEE401', 'Electric Motors'),
        ('1BEE402', 'Microcontroller'),
        ('1BEE403', 'Field Theory'),
        ('1BEE404', 'Transmission and Distribution'),
        ('1BEEL405', 'Electric Motors Lab'),
        ('1BEEL406A', 'Arduino, ARM & Raspberry Pi Based Projects'),
        ('1BEEL406B', 'Java Programming'),
        ('1BEEL406C', 'MATLAB'),
        ('1BEEL406D', 'Electrical Measurements Lab'),
        ('1BEE407', 'Biology for Electrical Engineers'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BEE409', 'Electric Power Generation and Economics'),
        ('1BMUS409', 'Music')
    ]
    for code, name in eee_4th:
        add_subject(conn, scheme_id, semesters[4], branches['EEE'], code, name, stream='electrical')
    
    # 5th Semester
    eee_5th = [
        ('1BEE501', 'Engineering Management and Entrepreneurship'),
        ('1BEE502', 'Signals and DSP'),
        ('1BEE503', 'Power Electronics'),
        ('1BEE504', 'Op-Amp and Linear Integrated Circuits'),
        ('1BEE505A', 'High Voltage Engineering'),
        ('1BEE505B', 'IoT and Embedded Systems'),
        ('1BEE505C', 'Electrical Drawing (CAD)'),
        ('1BEE505D', 'Programmable Logic Controllers'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BEEL507', 'Power Electronics Lab'),
        ('1BEE508', 'Hackathon-Based Project')
    ]
    for code, name in eee_5th:
        add_subject(conn, scheme_id, semesters[5], branches['EEE'], code, name, stream='electrical')
    
    # 6th Semester
    eee_6th = [
        ('1BEE601', 'Power System Analysis-I'),
        ('1BEE602', 'Control Systems'),
        ('1BEE603', 'Electric Vehicle Fundamentals'),
        ('1BEE604', 'Switchgear and Protection'),
        ('1BEE605A', 'Industrial Utilization of Electrical Power'),
        ('1BEE605B', 'Fundamentals of VLSI'),
        ('1BEE605C', 'Cyber Security'),
        ('1BEE605D', 'Drone Technology'),
        ('1BEEL606', 'PCC Lab'),
        ('1BEEL607A', 'Programmable Logic Controllers Lab'),
        ('1BEEL607B', 'Protection and High Voltage Lab'),
        ('1BEEL607C', 'IoT and Embedded Systems Lab'),
        ('1BEEL607D', 'Cyber Security Lab'),
        ('1BEE608', 'Capstone Project Phase-I'),
        ('1BEE609', 'Universal Human Value')
    ]
    for code, name in eee_6th:
        add_subject(conn, scheme_id, semesters[6], branches['EEE'], code, name, stream='electrical')
    
    # 7th Semester
    eee_7th = [
        ('1BEE701', 'Power System Analysis-II'),
        ('1BEE702A', 'Power System Operation and Control'),
        ('1BEE702B', 'Flexible AC Transmission Systems (FACTS)'),
        ('1BEE702C', 'AI Applications to Power System'),
        ('1BEE702D', 'Electric Vehicle Motors'),
        ('1BEE703A', 'UHVDC and UHVAC Transmission Systems'),
        ('1BEE703B', 'AI Applications to EVs'),
        ('1BEE703C', 'Battery Management in Electric Vehicles'),
        ('1BEE703D', 'Verilog and VHDL'),
        ('1BEE704A', 'Renewable Energy Sources'),
        ('1BEE704B', 'Utilization of Electrical Power'),
        ('1BEE704C', 'Energy Audit and Conservation'),
        ('1BEE704D', 'Foreign Language'),
        ('1BEE705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge System')
    ]
    for code, name in eee_7th:
        add_subject(conn, scheme_id, semesters[7], branches['EEE'], code, name, stream='electrical')
    
    # ==================== ECE Subjects ====================
    print("\n--- 2025 ECE Subjects ---")
    
    # 3rd Semester
    ece_3rd = [
        ('1BMAT301', 'Transform Techniques and Optimization Theory'),
        ('1BEC302', 'Digital System Design Using Verilog'),
        ('1BEC303', 'Network Analysis'),
        ('1BEC304', 'Analog Electronics and Linear Integrated Circuits'),
        ('1BEC305', 'Python Programming'),
        ('1BECL306', 'Analog Electronics and Linear Integrated Circuits Lab'),
        ('1BECL307A', 'Analog Electronic Circuit Simulations Lab'),
        ('1BECL307B', 'Microcontroller Lab'),
        ('1BEC307C', 'Introduction to Data Structures using Python Lab'),
        ('1BEC307D', 'Programming Using JAVA'),
        ('1BCP308', 'Community Project / Societal Project'),
        ('1BMUK309', 'Music')
    ]
    for code, name in ece_3rd:
        add_subject(conn, scheme_id, semesters[3], branches['ECE'], code, name, stream='electronics')
    
    # 4th Semester
    ece_4th = [
        ('1BEC401', 'Mathematics for Machine Learning'),
        ('1BEC402', 'Computer Organization and Microcontroller'),
        ('1BEC403', 'Signals and Systems'),
        ('1BEC404', 'Control Systems'),
        ('1BECL405', 'Signals and Control Lab'),
        ('1BECL406A', 'Debugging and Fault Analysis of Analog and Digital Circuits'),
        ('1BECL406B', 'IoT Lab'),
        ('1BECL406C', 'Basics of Machine Learning Lab'),
        ('1BECL406D', 'Sensors and Instrumentation Lab'),
        ('1BEC407', 'Programme Specific Biology'),
        ('1BEP408', 'Environmental Science Project'),
        ('1BEC409', 'Sensors and Measurements'),
        ('1BMUS409', 'Music')
    ]
    for code, name in ece_4th:
        add_subject(conn, scheme_id, semesters[4], branches['ECE'], code, name, stream='electronics')
    
    # 5th Semester
    ece_5th = [
        ('1BEC501', 'Economics and Management Course'),
        ('1BEC502', 'Digital Signal Processing'),
        ('1BEC503', 'Engineering Electromagnetics'),
        ('1BEC504', 'Introduction to VLSI Design'),
        ('1BEC505A', 'Machine Learning for Communication System'),
        ('1BEC505B', 'Real Time Systems'),
        ('1BEC505C', 'Bio-medical Instrumentation and Signal Processing'),
        ('1BEC505D', 'Semiconductor Process and Manufacturing Techniques'),
        ('1BRM506', 'Research Methodology and IPR'),
        ('1BECL507', 'VLSI Lab'),
        ('1BEC508', 'Hackathon-Based Project')
    ]
    for code, name in ece_5th:
        add_subject(conn, scheme_id, semesters[5], branches['ECE'], code, name, stream='electronics')
    
    # 6th Semester
    ece_6th = [
        ('1BEC601', 'Computer Networking and Communication'),
        ('1BEC602', 'Antenna and Wireless Communication'),
        ('1BEC603', 'Analog and Digital Communication'),
        ('1BEC604', 'FPGA Based System Design'),
        ('1BEC605A', '5G & 6G Communication Standards'),
        ('1BEC605B', 'Embedded Secure Element'),
        ('1BEC605C', 'Artificial Neural Networks & Deep Learning'),
        ('1BEC605D', 'Analog and Mixed Mode VLSI Design'),
        ('1BECL606', 'Communication Lab'),
        ('1BECL607A', 'PCB Design and Simulation using EDA Tools'),
        ('1BECL607B', 'Design of Sensor Boards for Applications'),
        ('1BECL607C', 'FPGA Computing Lab'),
        ('1BECL607D', 'Tools for Machine Learning and Deep Learning'),
        ('1BEC608', 'Capstone Project Phase-I'),
        ('1BEC609', 'Universal Human Value')
    ]
    for code, name in ece_6th:
        add_subject(conn, scheme_id, semesters[6], branches['ECE'], code, name, stream='electronics')
    
    # 7th Semester
    ece_7th = [
        ('1BEC701', 'Edge Computing with Tiny ML'),
        ('1BEC702A', 'RF Electronics'),
        ('1BEC702B', 'IoT Device Security'),
        ('1BEC702C', 'Image Processing and Pattern Recognition'),
        ('1BEC702D', 'Low Power VLSI'),
        ('1BEC703A', 'Digital Logic Verification with System Verilog'),
        ('1BEC703B', 'Cloud Computing'),
        ('1BEC703C', 'Automotive Technology'),
        ('1BEC703D', 'Cryptography & Network Security'),
        ('1BEC704A', 'Sensors and Actuators'),
        ('1BEC704B', 'Automotive Electronics'),
        ('1BEC704C', 'Consumer Electronics'),
        ('1BEC704D', 'Foreign Language'),
        ('1BEC705', 'Capstone Project Phase-II'),
        ('1BIKS706', 'Indian Knowledge Systems')
    ]
    for code, name in ece_7th:
        add_subject(conn, scheme_id, semesters[7], branches['ECE'], code, name, stream='electronics')
    
    if conn is None:
        conn.close()

def main():
    conn = init_connection()
    populate(conn)
    conn.close()
    print("\n2025 Scheme database populated successfully!")

if __name__ == "__main__":
    main()
