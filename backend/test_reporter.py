from reporter import TestReporter

# Reporter object initialize karo
reporter = TestReporter(project_name="WebTrace AI QA")

# Kuch dummy test results add karte hain (check karne ke liye)
reporter.add_test_result("Login Flow Validation", "PASS", "User successfully logged in with valid credentials.")
reporter.add_test_result("Dashboard Data Load", "FAIL", "API timeout while fetching user metrics.", "screenshots/error_load.png")

# Akanksha ke visual/DOM check ka data add karte hain
reporter.add_visual_bug("Navbar UI", "Alignment breaks on 1024px screen width", "High")

# Report generate karne ke commands
reporter.generate_json_report()
reporter.generate_markdown_report()

print("🎉 Success! Reports successfully generated check the reports folder.")