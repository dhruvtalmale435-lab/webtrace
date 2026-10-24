import json
import os
from datetime import datetime

class TestReporter:
    def __init__(self, project_name="WebTrace AI QA"):
        self.project_name = project_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.test_results = []
        self.visual_bugs = []

    def add_test_result(self, test_name, status, details, evidence_path=None):
        """Individual test step ya assertion ka result add karne ke liye"""
        self.test_results.append({
            "test_name": test_name,
            "status": status, # "PASS" ya "FAIL"
            "details": details,
            "evidence_path": evidence_path
        })

    def add_visual_bug(self, component, issue_description, severity="Medium"):
        """Akanksha ke visual auditor/DOM checks se mile bugs add karne ke liye"""
        self.visual_bugs.append({
            "component": component,
            "issue": issue_description,
            "severity": severity
        })

    def generate_json_report(self, output_path="reports/test_report.json"):
        """React Frontend dashboard ke liye JSON report generate karega"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report_data = {
            "project": self.project_name,
            "timestamp": self.timestamp,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": round(pass_rate, 2),
                "total_visual_bugs": len(self.visual_bugs)
            },
            "test_results": self.test_results,
            "visual_bugs": self.visual_bugs
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=4)
        
        return report_data

    def generate_markdown_report(self, output_path="reports/SUMMARY.md"):
        """GitHub ya local review ke liye Markdown summary generate karega"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["status"] == "PASS")
        
        md_content = f"""# 📊 Test Execution Report: {self.project_name}
* **Generated At:** {self.timestamp}
* **Total Tests:** {total_tests}
* **Passed:** {passed_tests}
* **Failed:** {total_tests - passed_tests}

---

## 🔍 Test Results
| Test Name | Status | Details / Evidence |
| :--- | :---: | :--- |
"""
        for t in self.test_results:
            status_icon = "✅ PASS" if t["status"] == "PASS" else "❌ FAIL"
            md_content += f"| {t['test_name']} | {status_icon} | {t['details']} |\n"

        md_content += """
---

## 🎨 Visual & DOM Audit (Akanksha's Module Integration)
| Component | Issue Description | Severity |
| :--- | :--- | :--- |
"""
        for b in self.visual_bugs:
            md_content += f"| {b['component']} | {b['issue']} | **{b['severity']}** |\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return output_path