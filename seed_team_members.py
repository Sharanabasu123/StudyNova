#!/usr/bin/env python3
"""
Script to populate the 3 fixed team members for StudyNova using SQLite directly
"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), 'studynova.db')

def seed_team_members():
    """Add the 3 fixed team members to the database"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    
    # Check if team members already exist
    cursor.execute("SELECT COUNT(*) as count FROM team_members")
    count = cursor.fetchone()['count']
    
    if count > 0:
        print(f"✓ Team members already exist: {count} members found")
        conn.close()
        return
    
    team_members = [
        {
            'name': 'Sharanabasu Malasidda Police Patil',
            'title': 'Founder & CEO',
            'role': 'Full Stack Developer | Platform Architect',
            'college': 'R. L. Jalappa Institute of Technology, Doddaballapur',
            'department': 'Computer Science & Engineering',
            'phone': '9108843309',
            'email': '',
            'bio': 'Sharanabasu Malasidda Police Patil is the Founder & CEO of StudyNova and the lead Full Stack Developer behind the platform. He designed and developed the architecture of StudyNova to provide VTU students with an organized platform for notes, lab programs, question papers, placement resources, and AI-powered learning tools. He is responsible for frontend development, backend development, database architecture, cloud integration, DevOps deployment, and continuous platform enhancement. He is a Final Year Computer Science and Engineering student at R. L. Jalappa Institute of Technology, Doddaballapur.',
            'github_url': 'https://github.com/Sharanabasu123',
            'linkedin_url': 'https://www.linkedin.com/in/sharanabasu-police-patil',
            'instagram_url': '',
            'sort_order': 1,
            'is_founder': 1,
        },
        {
            'name': 'Vamshi Krishna B N',
            'title': 'Developer',
            'role': 'Web Developer',
            'college': 'R. L. Jalappa Institute of Technology',
            'department': 'Computer Science & Engineering (Data Science)',
            'phone': '7411394737',
            'email': 'vkrishn79397@gmail.com',
            'bio': 'Vamshi Krishna B N contributes to the development of StudyNova by building modern web interfaces, improving user experience, and implementing new platform features. He actively supports frontend development, UI improvements, and platform optimization to ensure students have a smooth learning experience. He is a Computer Science and Engineering (Data Science) student at R. L. Jalappa Institute of Technology and is passionate about Artificial Intelligence, Data Analytics, and innovative software development.',
            'github_url': 'https://github.com/vamshi-krishna29',
            'linkedin_url': 'https://www.linkedin.com/in/vamshi-krishna-b-n-1283712a7',
            'instagram_url': '',
            'sort_order': 2,
            'is_founder': 0,
        },
        {
            'name': 'Megharaj',
            'title': 'Developer',
            'role': 'Full Stack Developer',
            'college': 'R. L. Jalappa Institute of Technology, Doddaballapur',
            'department': '',
            'phone': '+91 90364 45374',
            'email': 'megharajrathod58@gmail.com',
            'bio': 'Megharaj is a Full Stack Developer for StudyNova and contributes to backend development, feature implementation, testing, and system improvements. He collaborates on building reliable and scalable solutions to provide engineering students with an efficient academic platform. He is committed to enhancing StudyNova through modern web technologies and continuous innovation.',
            'github_url': '',
            'linkedin_url': '',
            'instagram_url': '',
            'sort_order': 3,
            'is_founder': 0,
        },
    ]
    
    for member in team_members:
        cursor.execute(f'''
            INSERT INTO team_members 
            (name, title, role, college, department, phone, email, bio, github_url, linkedin_url, instagram_url, sort_order, is_founder, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            member['name'],
            member['title'],
            member['role'],
            member['college'],
            member['department'],
            member['phone'],
            member['email'],
            member['bio'],
            member['github_url'],
            member['linkedin_url'],
            member['instagram_url'],
            member['sort_order'],
            member['is_founder'],
        ))
        print(f"✓ Added: {member['name']}")
    
    conn.commit()
    conn.close()
    print("\n✓ All 3 team members added successfully!")

if __name__ == '__main__':
    seed_team_members()
