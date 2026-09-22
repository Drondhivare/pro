import os
import re

tpl_dir = r'frontend/templates'
for root, _, files in os.walk(tpl_dir):
    for f in sorted(files):
        if not f.endswith('.html'):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, tpl_dir)
        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()
        
        has_inc_sidebar = 'components/sidebar.html' in content
        has_inc_navbar = 'components/navbar.html' in content
        
        sidebar_titles = re.findall(r'class="nav-section-title">([^<]+)<', content)
        user_roles = re.findall(r'class="user-role">([^<]+)<', content)
        require_auth = re.findall(r'Auth\.requireAuth\((.*?)\)', content)
        
        print(f'{rel}:')
        print(f'  include sidebar: {has_inc_sidebar}, navbar: {has_inc_navbar}')
        if sidebar_titles:
            print(f'  sidebar titles: {sidebar_titles}')
        if user_roles:
            print(f'  user roles: {user_roles}')
        if require_auth:
            print(f'  requireAuth: {require_auth}')
