import re
import os

def update_file(filename, patterns):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in patterns.items():
        new_content = re.sub(old, new, new_content)
        
    if new_content != content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
    else:
        print(f"No changes for {filename}")

# Jobs Views
jobs_patterns = {
    r"redirect\('job_list'\)": "redirect('jobs:job_list')",
    r"redirect\('my_jobs'\)": "redirect('jobs:my_jobs')",
    r"redirect\('job_detail'": "redirect('jobs:job_detail'",
    r"redirect\('my_applications'\)": "redirect('jobs:my_applications')",
}
update_file(r'c:\Users\USER\Downloads\omegaa-main\omegaa-main\jobs\views.py', jobs_patterns)

# Courses Views
courses_patterns = {
    r"redirect\('course_list'\)": "redirect('courses:course_list')",
    r"redirect\('course_detail'": "redirect('courses:course_detail'",
    r"redirect\('lesson_detail'": "redirect('courses:lesson_detail'",
    r"redirect\('complete_course'": "redirect('courses:complete_course'",
}
update_file(r'c:\Users\USER\Downloads\omegaa-main\omegaa-main\courses\views.py', courses_patterns)

# Chat Views
chat_patterns = {
    r"redirect\('chat_detail'": "redirect('chat:chat_detail'",
    r"redirect\('payment_plans'\)": "redirect('payments:payment_plans')",
}
update_file(r'c:\Users\USER\Downloads\omegaa-main\omegaa-main\chat\views.py', chat_patterns)

# Dashboard Views
dashboard_patterns = {
    r"redirect\('housekeeper_dashboard'\)": "redirect('dashboard:housekeeper_dashboard')",
    r"redirect\('employer_dashboard'\)": "redirect('dashboard:employer_dashboard')",
}
update_file(r'c:\Users\USER\Downloads\omegaa-main\omegaa-main\dashboard\views.py', dashboard_patterns)
