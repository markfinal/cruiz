#!/usr/bin/env python3

"""
Invoke github V4 API to query what was in a release
"""

import argparse
import json
import requests


def _request_data_from_github(token: str) -> str:
    """
    Query github for details
    """
    headers = {
        "Content-type": "application/json",
        "Authorization": f"bearer {token}",
    }

    query = """
    {
        repository(owner: "markfinal", name: "cruiz") {
            milestones(states: [OPEN], first: 100) {
                nodes {
                    title,
                    issues(states: [OPEN,CLOSED], first:100) {
                        nodes {
                            number,
                            title,
                            url,
                            state,
                            labels(first:10) {
                                nodes {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    response = requests.post(
        "https://api.github.com/graphql", headers=headers, json={"query": query}
    )
    response.raise_for_status()

    return response.json()


def _identify_issue_type(issue: dict) -> str:
    labels = issue["labels"]["nodes"]
    label_names = [i["name"] for i in labels]
    if "invalid" in label_names:
        return "other"
    if "wontfix" in label_names:
        return "wontfix"
    if "bug" in label_names:
        return "bug"
    if "enhancement" in label_names:
        return "enhancement"
    return "other"


def main(args) -> None:
    """
    Display formatted release notes for the specified release
    """
    try:
        github_data = _request_data_from_github(args.accesstoken)
    except requests.exceptions.HTTPError as exception:
        print(f"HTTP error: {exception}")
    except Exception as exception:
        print(f"Error: {exception}")
    else:
        if args.verbose:
            print(json.dumps(github_data, indent=4, sort_keys=True))

        repo_data = github_data["data"]["repository"]
        if repo_data is None:
            raise PermissionError("Repository data is empty. Was the access token valid?")

        try:
            milestones = repo_data["milestones"]["nodes"]
            version = [i for i in milestones if i["title"] == args.version]
            if version:
                issues = version[0]["issues"]["nodes"]
                bugs = []
                enhancements = []
                others = []
                open_issues = []
                for issue in issues:
                    if issue["state"] == "OPEN":
                        open_issues.append(issue)
                        continue
                    issue_type = _identify_issue_type(issue)
                    desc = (
                        f"Issue [{issue['number']}]({issue['url']}): {issue['title']}"
                    )
                    if issue_type == "bug":
                        bugs.append(desc)
                    elif issue_type == "enhancement":
                        enhancements.append(desc)
                    else:
                        others.append(desc)
                print(f"# Changes in version {args.version}")
                if bugs:
                    print("# Bugs fixed")
                    for bug in bugs:
                        print(bug)
                if enhancements:
                    print("# Enhancements")
                    for enhance in enhancements:
                        print(enhance)
                if others:
                    print("# Other fixes")
                    for other in others:
                        print(other)
                if open_issues:
                    print("********* WARNING: OPEN ISSUES IN MILESTONE ********")
                    for issue in open_issues:
                        print(issue)
            else:
                raise RuntimeError(f"Milestone {args.version} not found")
        except KeyError:
            if "errors" in github_data and not args.verbose:
                print(json.dumps(github_data, indent=4, sort_keys=True))
            else:
                raise


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("accesstoken", help="GitHub personal access token to use")
    PARSER.add_argument("version", help="Version of cruiz to generate release notes for")
    PARSER.add_argument(
        "-v", "--verbose", help="Display verbosely", action="store_true"
    )
    ARGS = PARSER.parse_args()
    main(ARGS)
