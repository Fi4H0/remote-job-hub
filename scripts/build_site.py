import os
import json
import hashlib

def build_dashboard():
    password = os.environ.get('SITE_PASSWORD', 'Admin123!')
    hashed_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()

    jobs_file = 'data/jobs.json'
    if os.path.exists(jobs_file):
        with open(jobs_file, 'r', encoding='utf-8') as f:
            jobs_data = f.read()
    else:
        jobs_data = "[]"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote PM & Service Delivery Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <!-- LOGIN MODAL -->
    <div id="login-modal" class="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div class="bg-gray-800 p-6 rounded-xl border border-gray-700 max-w-sm w-full">
            <h2 class="text-xl font-bold mb-4 text-center">🔐 Access Restricted</h2>
            <input type="password" id="password-input" placeholder="Enter Password" class="w-full p-2.5 rounded bg-gray-700 border border-gray-600 mb-4 focus:outline-none focus:border-indigo-500 text-white">
            <button onclick="authenticate()" class="w-full bg-indigo-600 hover:bg-indigo-500 py-2.5 rounded font-semibold transition">Login</button>
            <p id="error-msg" class="text-red-400 text-xs mt-2 hidden text-center">Invalid password</p>
        </div>
    </div>

    <!-- MAIN DASHBOARD -->
    <div id="dashboard" class="hidden max-w-6xl mx-auto p-6">
        <header class="flex justify-between items-center mb-6 pb-4 border-b border-gray-800">
            <div>
                <h1 class="text-2xl font-bold text-indigo-400">Remote Tech PM & Delivery Hub</h1>
                <p class="text-sm text-gray-400">Aggregated from FlexJobs, We Work Remotely, Himalayas, Remote OK, LinkedIn</p>
            </div>
            <button onclick="logout()" class="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded border border-gray-700">Logout</button>
        </header>

        <div id="jobs-container" class="space-y-4"></div>
    </div>

    <script>
        const EXPECTED_HASH = "{hashed_pw}";
        const JOBS = {jobs_data};

        async function hashSHA256(str) {{
            const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
            return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
        }}

        async function authenticate() {{
            const input = document.getElementById('password-input').value;
            const inputHash = await hashSHA256(input);
            if (inputHash === EXPECTED_HASH) {{
                sessionStorage.setItem('auth', 'true');
                showDashboard();
            }} else {{
                document.getElementById('error-msg').classList.remove('hidden');
            }}
        }}

        function logout() {{
            sessionStorage.removeItem('auth');
            location.reload();
        }}

        function showDashboard() {{
            document.getElementById('login-modal').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
            renderJobs();
        }}

        function renderJobs() {{
            const container = document.getElementById('jobs-container');
            if (!JOBS.length) {{
                container.innerHTML = `<p class="text-gray-400">No jobs found matching your criteria in the past 7 days.</p>`;
                return;
            }}
            container.innerHTML = JOBS.map(j => `
                <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-start">
                    <div>
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">${{j.source}}</span>
                        <h3 class="text-lg font-bold mt-1 text-white">${{j.title}}</h3>
                        <p class="text-sm text-gray-400">${{j.company}} • <span class="text-gray-300">${{j.location}}</span></p>
                        <p class="text-xs text-gray-500 mt-2 line-clamp-2">${{j.snippet}}</p>
                    </div>
                    <a href="${{j.url}}" target="_blank" class="bg-indigo-600 hover:bg-indigo-500 text-xs px-3 py-2 rounded text-white font-medium ml-4 shrink-0">Apply</a>
                </div>
            `).join('');
        }}

        if (sessionStorage.getItem('auth') === 'true') showDashboard();
    </script>
</body>
</html>"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("Compiled static website index.html successfully.")

if __name__ == "__main__":
    build_dashboard()