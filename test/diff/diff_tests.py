import argparse
import csv
import logging
import os

from custom_json_diff.lib.custom_diff import compare_dicts, perform_bom_diff, report_results
from custom_json_diff.lib.custom_diff_classes import Options
from custom_json_diff.lib.utils import json_dump

from generate import filter_repos

logging.disable(logging.INFO)


def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--directories',
        '-d',
        default=['/home/runner/work/original_snapshots', '/home/runner/work/new_snapshots'],
        help='Directories containing the snapshots to compare',
        nargs=2
    )
    parser.add_argument(
        '--projects',
        '-p',
        help='Filter to these projects.',
        dest='projects',
    )
    parser.add_argument(
        '--types',
        '-t',
        help='Filter to these project types.',
        dest='project_types',
    )
    return parser.parse_args()


def compare_snapshot(dir1, dir2, options, repo):
    bom_1 = f"{dir1}/{repo['project']}-bom.json"
    bom_2 = f"{dir2}/{repo['project']}-bom.json"
    options.file_1 = bom_1
    options.file_2 = bom_2
    options.output = f'{dir2}/{repo["project"]}-diff.json'
    if not os.path.exists(bom_1):
        return 1, f'{bom_1} not found.', f'{bom_1} not found.'
    status, j1, j2 = compare_dicts(options)
    if status != 0:
        status, result_summary = perform_bom_diff(j1, j2)
        if status != 0:
            report_results(status, result_summary, options, j1, j2)
            return status, f"{repo['project']} failed.", result_summary
    return status, None, None


def perform_snapshot_tests(dir1, dir2, projects, project_types):
    repo_data = read_csv(projects, project_types)

    options = Options(
        allow_new_versions=True,
        allow_new_data=True,
        preconfig_type="bom",
        include=["properties", "evidence", "licenses"],
    )

    failed_diffs = {}
    for repo in repo_data:
        status, result, summary = compare_snapshot(dir1, dir2, options, repo)
        if result:
            print(result)
        if status != 0:
            failed_diffs[repo["project"]] = summary

    if failed_diffs:
        diff_file = os.path.join(dir2, 'diffs.json')
        json_dump(diff_file, failed_diffs)
        print(f"Results of failed diffs saved to {diff_file}")
    else:
        print("Snapshot tests passed!")


def read_csv(projects, project_types):
    csv_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "repos.csv")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        repo_data = list(reader)
    return filter_repos(repo_data, projects, project_types)


if __name__ == '__main__':
    args = build_args()
    if args.project_types:
        if ',' in args.project_types:
            project_types = set(args.project_types.split(','))
        else:
            project_types = {args.project_types}
    else:
        project_types = None
    perform_snapshot_tests(args.directories[0], args.directories[1], args.projects, project_types)
