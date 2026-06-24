# StudyNova Admin Upload Issue - Debug Tools Guide

## Quick Start

### Access Debug Tools (Admin Only)
1. Login as admin
2. Copy these URLs and visit them:

```
/debug/data-summary      → Overview of database contents
/debug/test-flow         → Step-by-step upload flow test
/debug/subjects          → View and filter subjects
/debug/resources         → View and filter resources
```

---

## 🔍 Debug Route 1: `/debug/data-summary`

### What It Shows
- Total records in each table (schemes, semesters, branches, subjects, resources)
- Data quality checks (orphaned resources, subjects with resources)
- Sample data from each table

### When to Use
- First step: Verify database has data
- Check overall health of the system
- Identify if resources are properly approved

### What Good Data Looks Like
```
Schemes: 3
Semesters: 12
Branches: 4
Subjects: 50
Resources: 150
Approved Resources: 150
Orphaned Resources: 0
```

### What Bad Data Looks Like
```
Schemes: 3
Semesters: 12
Branches: 4
Subjects: 0              ← PROBLEM: No subjects!
Resources: 5
Approved Resources: 0    ← PROBLEM: Resources not approved!
Orphaned Resources: 5    ← PROBLEM: Orphaned resources found!
```

---

## 🧪 Debug Route 2: `/debug/test-flow`

### What It Does
Simulates the complete upload and retrieval flow:
1. Select Scheme
2. Select Semester
3. Select Branch (optional)
4. Select Subject
5. View Resources

### When to Use
- Test complete upload workflow
- Identify exactly where filtering breaks
- Verify step-by-step data retrieval

### How to Use

**Step 1**: Visit `/debug/test-flow`

**Step 2**: Select Scheme
- Choose: "2022 Scheme"
- Notice counter: "Semesters Available: 8"

**Step 3**: Select Semester
- Choose: "3rd Semester"
- Notice counter: "Subjects Available: 12"

**Step 4**: Select Branch
- Choose: "CSE"
- Notice counter: "Subjects Available: 4" (filtered)

**Step 5**: Select Subject
- Choose: Any subject
- Notice counter: "Resources Available: 3"

**Step 6**: View Resources
- Should see uploaded materials listed
- If empty: resources haven't been uploaded yet

### Troubleshooting

**Problem: "Subjects Available: 0"**
- Root cause: No subjects for that scheme/semester/branch
- Solution: Check `/debug/subjects?scheme_id=1&semester_id=5`

**Problem: "Resources Available: 0"**
- Root cause: No resources uploaded for that subject
- Solution: Check if admin uploaded anything
- Or: Resources are not approved (check is_approved=0)

---

## 🔎 Debug Route 3: `/debug/subjects`

### What It Shows
All subjects with complete details:
- Subject ID, Code, Name
- Linked Scheme/Semester/Branch IDs
- Linked Scheme/Semester/Branch Names
- Stream and Common flag

### When to Use
- Verify subjects are linked to correct scheme/semester/branch
- Find subjects for a specific selection
- Check is_common flag

### How to Use

**View All Subjects**:
- Visit `/debug/subjects`
- Scroll through complete list
- All rows have yellow background (not filtered)

**Filter by Scheme**:
- Visit `/debug/subjects?scheme_id=1`
- Enter: Scheme ID = 1
- Click: Filter
- Shows only subjects for that scheme

**Filter by Scheme + Semester**:
- Visit `/debug/subjects?scheme_id=1&semester_id=5`
- Enter: Both IDs
- Click: Filter
- Shows intersection

**Filter by Branch**:
- Enter: Branch ID = 3
- Click: Filter
- Shows subjects for that branch (or is_common=1)

### Reading the Table

| Column | Meaning |
|--------|---------|
| ID | Subject primary key |
| Code | Subject code (e.g., "18CS02") |
| Name | Subject name (e.g., "Data Structures") |
| scheme_id | Link to schemes table |
| semester_id | Link to semesters table |
| branch_id | Link to branches table |
| Scheme | Name of linked scheme |
| Semester | Name of linked semester |
| Branch | Name of linked branch |
| Common | If 1: available to all branches |
| Stream | Stream code (e.g., "computer_science") |

---

## 📦 Debug Route 4: `/debug/resources`

### What It Shows
All resources with complete details:
- Resource ID, Title
- Linked Subject Name
- Resource Type, Approved Status
- Uploader Name, Upload Date
- View/Download Counts

### When to Use
- Verify uploaded resources exist
- Check approval status
- Find resources by subject

### How to Use

**View All Resources**:
- Visit `/debug/resources`
- Scroll through list
- Green rows = approved, Yellow rows = not approved

**Filter by Subject**:
- Visit `/debug/resources?subject_id=42`
- Enter: Subject ID = 42
- Click: Filter
- Shows only resources for that subject

**Filter for Approved Only**:
- Visit `/debug/resources?approved_only=yes`
- Shows only is_approved=1 resources
- Yellow rows disappear

**Filter Approved + Subject**:
- Visit `/debug/resources?subject_id=42&approved_only=yes`
- Shows approved resources for that subject only

### Reading the Table

| Column | Meaning |
|--------|---------|
| ID | Resource primary key |
| Title | Resource name (e.g., "Data Structures - Module 1 Notes") |
| Subject | Name of subject it's linked to |
| subject_id | Raw subject ID (for debugging) |
| Type | Resource type (module1, pyq, solutions, etc.) |
| Approved | Yes (green) = will show to students, No (yellow) = hidden |
| Uploaded By | Username of admin who uploaded |
| Date | Upload date |
| Views | How many times viewed |
| Downloads | How many times downloaded |

---

## 📊 Console Output

When a student or admin visits `/notes`, debug output appears in the console:

```
[DEBUG] /notes - scheme_id=1, semester_id=5, branch_id=3, subject_id=null
[DEBUG] Filtered semesters for scheme 1: 8 found
[DEBUG] Filtered subjects query - where_clause: s.scheme_id = ? AND s.semester_id = ? AND (...), params: [1, 5, 3]
[DEBUG] Filtered subjects: 4 found
[DEBUG] Sample subject: {'id': 42, 'name': 'Data Structures', 'code': '18CS02', 'scheme_id': 1, ...}
```

### Reading Console Output

**✅ Good Output**:
```
Filtered subjects: 4 found
Resources for subject 42: 3 found
```

**❌ Bad Output**:
```
Filtered subjects: 0 found        ← No subjects returned
Resources for subject 42: 0 found ← No resources
```

---

## Common Issues & Quick Fixes

### Issue 1: No subjects shown
```
Visit: /debug/subjects?scheme_id=1&semester_id=5
If empty: Subjects don't exist for that combination
Fix: Use admin panel to add subjects
```

### Issue 2: Subjects shown but no resources
```
Visit: /debug/resources?subject_id=42&approved_only=yes
If empty: Either no uploads or not approved
Fix: Check /admin/notes to see if upload succeeded
```

### Issue 3: Resources exist but students can't see
```
Visit: /debug/resources?subject_id=42
Check: Approved column
If "No": Admin needs to approve resources
Fix: Go to /admin/notes/edit/[resource_id] and approve
```

### Issue 4: Wrong data appearing
```
Console output shows:
[DEBUG] Filtered subjects: 10 found
But student sees: "No subjects found"

Root cause: JavaScript type mismatch (fixed)
Try: Hard refresh (Ctrl+Shift+R) browser cache
```

---

## Database Verification

For advanced users, run these SQL commands:

```sql
-- Check if data exists
SELECT COUNT(*) as subjects FROM subjects;
SELECT COUNT(*) as resources FROM resources WHERE is_approved=1;

-- Check linking
SELECT r.subject_id, COUNT(*) as resources_count
FROM resources r
WHERE r.is_approved = 1
GROUP BY r.subject_id;

-- Find problems
SELECT * FROM resources WHERE is_approved = 0;
SELECT * FROM resources WHERE subject_id NOT IN (SELECT id FROM subjects);
```

---

## Need More Help?

1. **For data summary**: Visit `/debug/data-summary`
2. **For step-by-step test**: Visit `/debug/test-flow`
3. **For subject details**: Visit `/debug/subjects`
4. **For resource details**: Visit `/debug/resources`
5. **For console logs**: Open browser Developer Tools (F12)

---

**Last Updated**: June 24, 2026  
**Version**: 1.0  
**Status**: ✅ Ready to Use
