"""Measures classifier and router accuracy on the test CSVs (no Gmail, no monday)."""

import argparse
import csv
import os

import classifier
import router

DEFAULT_FILES = [
    "test-data/heido_test_cases.csv",
    "test-data/heido_holdout_cases.csv",
]
FIELDS = ["category", "priority", "assignee"]


def evaluate_row(row, file_name):
    """Classify one test email and compare it to the expected values.

    Args:
        row: one CSV row as a dict (test_id, subject, body, expected_*, ...).
        file_name: the CSV file name, saved with the result.

    Returns:
        A dict with expected and actual values for each field, plus "error"
        (empty if the call worked). A failed row counts as a miss.
    """
    result = {"file": file_name, "test_id": row["test_id"], "what_it_tests": row["what_it_tests"]}
    for field in FIELDS:
        result[f"expected_{field}"] = row[f"expected_{field}"]
        result[f"actual_{field}"] = ""
    result["error"] = ""

    try:
        classification = classifier.classify(row["subject"], row["body"])
        result["actual_category"] = classification.category
        result["actual_priority"] = classification.priority
        result["actual_assignee"] = router.assign(classification.category)
    except Exception as error:  # keep going: one failed row must not stop the run
        result["error"] = str(error)
    return result


def evaluate_file(path):
    """Evaluate every row in one CSV file, printing a progress line per row.

    Args:
        path: path to a test CSV (UTF-8 with BOM).

    Returns:
        A list of result dicts, one per row.
    """
    file_name = os.path.basename(path)
    print(f"\nRunning {file_name} ...")
    results = []
    # utf-8-sig skips the BOM, so the first column is "test_id", not "﻿test_id".
    with open(path, encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            result = evaluate_row(row, file_name)
            results.append(result)
            if result["error"]:
                status = f"ERROR: {result['error']}"
            else:
                status = "  ".join(f"{field} {'OK' if is_match(result, field) else 'MISS'}" for field in FIELDS)
            print(f"  {result['test_id']}  {status}")
    return results


def is_match(result, field):
    """Return True if the actual value of a field equals the expected value."""
    return result[f"actual_{field}"] == result[f"expected_{field}"]


def print_report(title, results):
    """Print the accuracy for each field, the errors and the mismatches.

    Rows that failed with an error are left out of the accuracy, so the
    numbers reflect only the AI's answers.

    Args:
        title: the heading, e.g. a file name or "Combined".
        results: a list of result dicts from evaluate_row.
    """
    answered = [result for result in results if not result["error"]]
    failed = [result for result in results if result["error"]]

    print(f"\n=== {title} ({len(results)} emails) ===")
    if answered:
        for field in FIELDS:
            correct = sum(1 for result in answered if is_match(result, field))
            print(f"  {field.capitalize():<9} {correct}/{len(answered)}  {correct / len(answered):.0%}")
    else:
        print("  No successful rows, so no accuracy.")
    print(f"  Errors: {len(failed)} (excluded from accuracy)")

    if failed:
        print("  Error details:")
        for result in failed:
            print(f"    {result['test_id']}  {result['error'][:120]}")

    mismatches = [
        (result, field) for result in answered for field in FIELDS if not is_match(result, field)
    ]
    if not mismatches:
        print("  No mismatches.")
        return
    print("  Mismatches:")
    for result, field in mismatches:
        print(f"    {result['test_id']}  {field}: expected {result[f'expected_{field}']!r}, "
              f"got {result[f'actual_{field}']!r}  [{result['what_it_tests']}]")


def save_results(results, path):
    """Write all results to a CSV file.

    Args:
        results: a list of result dicts from evaluate_row.
        path: the output CSV path.
    """
    with open(path, "w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved {len(results)} results to {path}")


def main():
    """Read the command-line options, evaluate each file, print the reports."""
    parser = argparse.ArgumentParser(description="Measure Heido classification accuracy.")
    parser.add_argument("files", nargs="*", default=DEFAULT_FILES,
                        help="test CSV files (default: both files in test-data/)")
    parser.add_argument("--out", help="save all results to this CSV file")
    args = parser.parse_args()

    results_per_file = {path: evaluate_file(path) for path in args.files}
    all_results = [result for results in results_per_file.values() for result in results]

    for path, results in results_per_file.items():
        print_report(os.path.basename(path), results)
    print_report("Combined", all_results)

    if args.out:
        save_results(all_results, args.out)


if __name__ == "__main__":
    main()
