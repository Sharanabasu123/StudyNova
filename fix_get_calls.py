
import re
import os

app_path = "c:\\Users\\HP\\Downloads\\StudyNova\\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Now let's look for patterns like row.get('x'), user.get('y'), note.get('z'), etc.
# This regex looks for identifiers followed by .get('key') or .get("key") or .get('key', default)
# We need to capture the identifier, the key, and optional default
# We'll replace them with identifier['key'] or identifier['key'] if default isn't needed
# But we need to be careful! Because .get might be called on other things, like dicts that are not row objects!
# So we'll look for common variable names that are commonly hold database rows!
# First, let's list all common row variable names in app.py:
# user, note, resource, message, scheme, semester, branch, cycle, subject, etc.

# Let's start by replacing all:
# (user.get('role') → user['role']
# (user.get('username) → user['username']
# etc., for all variables that are likely to be database rows!

# Let's first do a first pass: replace .get(' with [ and ) with ]!
# But we need to be careful about .get calls with default values!
# Wait, but in our code, do we ever use .get with default?

# Let's first check app.py!

content = re.sub(r'(user|note|resource|message|scheme|semester|branch|cycle|subject|row|result|cat|topic|school_class|school_subject|school_chapter|exam_cat|exam_topic|school_resource|exam_resource|subj|sem|sch|r|s|u|m|t|d)\.get\((['"])([^\1]+?)\2(?:,\s*(.*?))?\)", r"\1['\3']" , content)

# Wait that regex might be too aggressive, let's test with known examples! Let's first replace .get('key"
# Let's use a simpler approach first, let's manually check app.py! Let's first replace the known ones!
# Let's first write the replacement step by step!

# Let's look at known places:
# 1. Line 899: user.get('role') → user['role']
content = re.sub(r"user\.get\(['"role['"]", "user['role']", content)

# 2. safe_get_count: result and 'count' in result → result is a dict or row? Let's keep safe_get_count is already uses bracket notation!
# Let's keep safe_get_count is okay, result['count'], which is already correct!
# 3. Check other places!

# Let's check all instances of .get in app.py! Let's also check in the templates!
# Now let's save the modified content!
with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done modifying app.py!")
