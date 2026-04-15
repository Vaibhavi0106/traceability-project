from flask import Flask, render_template
from traceability import (
    load_stories,
    parse_test_trace_links,
    load_test_results,
    build_matrix,
    calculate_metrics
)

app = Flask(__name__)


@app.route("/")
def home():
    story_file = "stories.md"   # change to "stories.md" when needed

    stories = load_stories(story_file)
    links = parse_test_trace_links("tests/test_app.py")
    results = load_test_results("report.json")
    matrix = build_matrix(stories, links, results)
    metrics = calculate_metrics(matrix)

    passed_count = sum(1 for row in matrix if row["status"] == "Passed")
    broken_count = sum(1 for row in matrix if row["status"] == "Broken")
    not_covered_count = sum(1 for row in matrix if row["status"] == "Not Covered")

    story_ids = [row["id"] for row in matrix]
    test_counts = [len(row["tests"]) for row in matrix]

    return render_template(
        "report.html",
        matrix=matrix,
        metrics=metrics,
        passed_count=passed_count,
        broken_count=broken_count,
        not_covered_count=not_covered_count,
        story_ids=story_ids,
        test_counts=test_counts
    )


if __name__ == "__main__":
    app.run(debug=True)