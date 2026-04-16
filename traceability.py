import yaml
import json
import re
import csv
import os
import sys

def load_stories(file_path):
    _, ext = os.path.splitext(file_path.lower())

    if ext in [".yaml", ".yml"]:
        return load_stories_from_yaml(file_path)
    elif ext == ".md":
        return load_stories_from_markdown(file_path)
    else:
        raise ValueError("Unsupported story file format. Use YAML, YML, or MD.")


def load_stories_from_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["stories"]


def load_stories_from_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"##\s*(US-\d+):\s*(.+?)\n(.*?)(?=\n##\s*US-\d+:|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)

    stories = []
    for story_id, title, description in matches:
        stories.append({
            "id": story_id.strip(),
            "title": title.strip(),
            "description": description.strip().replace("\n", " ")
        })

    return stories


def parse_test_trace_links(test_file):
    links = []
    current_story = None

    with open(test_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        trace_match = re.search(r"TRACE:\s*(US-\d+)", line)
        test_match = re.search(r"def\s+(test_\w+)\(", line)

        if trace_match:
            current_story = trace_match.group(1)

        if test_match and current_story:
            test_name = test_match.group(1)
            links.append({
                "story_id": current_story,
                "test_name": test_name
            })
            current_story = None

    return links


def load_test_results(report_file):
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = {}

    for test in data.get("tests", []):
        nodeid = test.get("nodeid", "")
        outcome = test.get("outcome", "")
        test_name = nodeid.split("::")[-1]
        results[test_name] = outcome

    return results


def build_matrix(stories, links, test_results):
    matrix = []

    for story in stories:
        sid = story["id"]
        linked_tests = [l["test_name"] for l in links if l["story_id"] == sid]

        if not linked_tests:
            status = "Not Covered"
        else:
            outcomes = [test_results.get(t, "unknown") for t in linked_tests]

            if "failed" in outcomes:
                status = "Broken"
            elif all(o == "passed" for o in outcomes):
                status = "Passed"
            else:
                status = "Unknown"

        matrix.append({
            "id": sid,
            "title": story["title"],
            "description": story["description"],
            "tests": linked_tests,
            "status": status
        })

    return matrix


def calculate_metrics(matrix):
    total = len(matrix)
    covered = sum(1 for m in matrix if len(m["tests"]) > 0)
    uncovered = sum(1 for m in matrix if m["status"] == "Not Covered")
    broken = sum(1 for m in matrix if m["status"] == "Broken")
    passed = sum(1 for m in matrix if m["status"] == "Passed")
    coverage = (covered / total) * 100 if total > 0 else 0

    return {
        "total_stories": total,
        "covered_stories": covered,
        "uncovered_stories": uncovered,
        "broken_stories": broken,
        "passed_stories": passed,
        "coverage_percent": round(coverage, 2)
    }


def export_csv(matrix, filename="traceability_matrix.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Story ID", "Title", "Description", "Linked Tests", "Status"])

        for row in matrix:
            writer.writerow([
                row["id"],
                row["title"],
                row["description"],
                ", ".join(row["tests"]) if row["tests"] else "No linked tests",
                row["status"]
            ])


if __name__ == "__main__":
    story_file = "stories.md"   # change to stories.yaml if you want YAML

    stories = load_stories(story_file)
    links = parse_test_trace_links("tests/test_app.py")
    results = load_test_results("report.json")
    matrix = build_matrix(stories, links, results)
    metrics = calculate_metrics(matrix)

    export_csv(matrix)

    print("\nTRACEABILITY REPORT")
    print("-------------------")
    for row in matrix:
        print(f"{row['id']} | {row['title']} | {row['tests']} | {row['status']}")

    print("\nMETRICS")
    print("-------")
    print(f"Total Stories: {metrics['total_stories']}")
    print(f"Covered Stories: {metrics['covered_stories']}")
    print(f"Uncovered Stories: {metrics['uncovered_stories']}")
    print(f"Broken Stories: {metrics['broken_stories']}")
    print(f"Passed Stories: {metrics['passed_stories']}")
    print(f"Coverage: {metrics['coverage_percent']}%")
    if metrics["broken_stories"] > 0:
    print("\nCI CHECK FAILED: Broken requirements detected.")
    sys.exit(1)