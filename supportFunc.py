from multiprocessing.sharedctypes import Value
import random
import re
import csv
from tkinter.filedialog import askopenfilenames


def confidenceThreshold(prediction_list):
    """
    Take in a list of dictionaries stored as prediction_list and order it according to the following structure:
        1. All failed tests
        2. Confidence: low to high

    Each dictionary in the list has a key for “prediction” which is either the string “SUCCESS” or “FAILURE”. Each dictionary has a key for “confidence” which is a number 0-1. 1 being 100% confident and 0 being 0% confident.

    Sort the list to have all failed tests at the start of the list and then have the lowest confident tests next. The end of the list therefore has the highest confidence test prediction.

    return(sorted_prediction_list)

    """
    return sorted(prediction_list, key=lambda x: (x["prediction"], x["confidence"]))


def loadFiles(File_Type):
    # THIS FUNCTION NEEDS TO CHANGE TO ACCEPT A PATH W/O HUMAN INTERACTION
    # A command line argument perhaps?
    # Ideally, it would point to a directory full of the stuff we need, and just let us run model.py /diffs/directory /tests/directory
    file_names = askopenfilenames(title=File_Type, filetypes=[("Data", ("*.csv"))])
    # print(file_names)
    return file_names


def versionMatch():
    """
    Take in path to a directory for diffs, and one for tests, return dictionary with diffs matched to test sets.

    """
    diffs = loadFiles("Diff csvs")
    tests = loadFiles("Test csvs")

    output = dict()
    for diff in diffs:
        # Each dictionary value is an array, [*path to diff*, [*array of paths to tests*]]
        output[re.findall("\d+_\d+_\d+_\d+", diff)[0]] = [diff, []]

    for test in tests:
        try:
            output[re.findall("\d+_\d+_\d+_\d+", test)[0]][1].append(test)
        except:  # If no match is found
            print(
                f"Path :{test}\n This path does not appear to be a file with correctly formatted version number in it's path."
            )
            continue

    return output


class TestStruct:
    def __init__(self, name):
        self.name = name
        self.current_score = -1
        # Array of tuples, one with result, one with machine, if any.
        self.tests = []
        # Historical pass fail rate, dummy value for now
        self.historical = 0.5

    def __eq__(self, other):
        if self.name == other:
            return True
        else:
            return False

    def __repr__(self):
        return f"TestStruct: {self.name}"


def condenseTests(vM_dict):
    """
    Take in matched set from versionMatch(), load into TestStruct for averaging

    vM_dict == versionMatch() return value

    return:
    dict with version # as keys
    dict as values
    values hold:
    test name as key
    test struct as value
    """
    output = dict()

    lines_processed = 0
    for k, v in vM_dict.items():
        output[k] = dict()
        for test_csv in v[1]:
            with open(test_csv, "r", encoding="utf8") as csv_file:
                current = csv.DictReader(csv_file)
                for row in current:
                    lines_processed += 1
                    if (
                        row["result"] == "skipped"
                        or row["result"] == "untested"
                        # row["result"]
                        # == "ABORTED"
                    ):  # Don't let skipped test effect weight
                        continue

                    if row["test_name"] not in output:
                        # create new
                        output[k][row["test_name"]] = TestStruct(row["test_name"])
                    # update existing/give current values
                    if row["instrument_name"] is not None:
                        output[k][row["test_name"]].tests.append(
                            (row["result"], row["instrument_name"])
                        )
                    else:
                        output[k][row["test_name"]].tests.append((row["result"], None))
            print(f"Lines processed: {lines_processed}")
    return output


def loadDiffs(vM_dict):
    """
    Take in matched set from version match, output diffs info dict with version as k, dict as value.

    Each value has this format:
    total_change
    total_add
    total_del
    total_fchange
    files : array of dicts
        name
        extension
        file_change
        file_add
        file_del
    """
    output = dict()

    for k, v in vM_dict.items():
        current = dict()
        with open(v[0], "r", encoding="utf8") as target:
            diff = csv.DictReader(target)
            file_changes = []

            for row in diff:
                current["total_change"] = row["total changes for diff"]
                current["total_add"] = row["total addtions for diff"]
                current["total_del"] = row["total deletions for diff"]
                current["total_fchange"] = row["total number of files changed for diff"]
                current_file = dict()
                current_file["name"] = row["Filename"]
                current_file["extension"] = row["file extension"]
                current_file["file_change"] = row["total changes for file"]
                current_file["file_add"] = row["total additions for file"]
                current_file["file_del"] = row["total deletions for file"]
                file_changes.append(current_file)

            current["files"] = file_changes
            output[k] = current

    return output


if __name__ == "__main__":
    # Informal test for versionMatch
    # diffs_paths = askopenfilenames(title="Select file", filetypes=[("Data", ("*.csv"))])
    # test_paths = askopenfilenames(title="Select file", filetypes=[("Data", ("*.csv"))])

    result = versionMatch()

    diffs = dict()

    for k, v in result.items():
        diffs[k] = loadDiffs(v[0])

    # for k, v in diffs.items():
    #     print(f"{k}:")
    #     for i, j in v.items():
    #         print(i, j)

    # ***Output pass/fail info***
    # condensed_tests = condenseTests(result)

    # print(f"number of tests: {len(condensed_tests)}")

    # for diffk, diffv in condensed_tests.items():
    #     pass_count = 0
    #     fail_count = 0
    #     weird = 0
    #     for testk, testv in diffv[1].items():
    #         for test_case in testv.tests:
    #             if test_case[0] == "passed":
    #                 # test_case[0] == "SUCCESS":
    #                 pass_count += 1
    #             elif test_case[0] == "failed":
    #                 # test_case[0] == "FAILURE":
    #                 fail_count += 1
    #             else:
    #                 print(test_case[0])
    #     print(f"{diffk}: passed: {pass_count}, failed: {fail_count}")

    # # Informal test for confidenceThreshold
    # test_list = []
    # for i in range(50):
    #     test_list.append(
    #         {
    #             "prediction": "SUCCESS" if random.randint(0, 1) else "FAILURE",
    #             "confidence": random.random(),
    #         }
    #     )
    # result = confidenceThreshold(test_list)
    # for thing in result:
    #     print(thing)
