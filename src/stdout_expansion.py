import re

"""

%J = jobid.stepid of the running job. (e.g. "128.0")
%N = short hostname. This will create a separate IO file per node.
%n = Node identifier relative to current job (e.g. "0" is the first node of the running job) This will create a separate IO file per node.
%s = stepid of the running job.
%t = task identifier (rank) relative to current job. This will create a separate IO file per task.

'\\' = Do not process any of the replacement symbols.

A number placed between the percent character and format specifier may be used to zero-pad the result in the IO filename to at minimum of
specified numbers. This number is ignored if the format specifier corresponds to non-numeric data (%N for example).
The maximal number is 10, if a value greater than 10 is used the result is padding up to 10 characters.
"""


def replace_jobid(filename, job_id):
    matches = re.finditer(r"%(\d*)J", filename)
    filename = _replace_number(filename, matches, job_id)
    return filename


def replace_hostname(filename, hostname):
    matches = re.finditer(r"%(\d*)N", filename)
    filename = _replace_string(filename, matches, hostname)
    return filename


def replace_node_id(filename, node_id):
    matches = re.finditer(r"%(\d*)n", filename)
    filename = _replace_number(filename, matches, node_id)
    return filename


def replace_stepid(filename, step_id):
    matches = re.finditer(r"%(\d*)s", filename)
    filename = _replace_string(filename, matches, step_id)
    return filename


def replace_taskid(filename, task_id):
    matches = re.finditer(r"%(\d*)t", filename)
    filename = _replace_number(filename, matches, task_id)
    return filename


def _replace_number(filename, matches, number):
    # Loop through the matches
    for match in matches:
        # if there's padding, use it
        if match.group(1):
            # only pad up to 10 zeros
            padding = min(int(match.group(1)), 10)
            num = number.zfill(padding)
        else:
            num = number

        # Replace the match with the (padded) number
        filename = filename.replace(match.group(0), str(num))

    return filename


def _replace_string(filename, matches, string):
    # Loop through the matches
    for match in matches:
        # Replace the match with the hostname, padding is ignored
        filename = filename.replace(match.group(0), string)

    return filename


"""
Note: This implementation is based on best effort, as the string stored in
scontrol does not consistently match the actual filename. The string in
scontrol expands all specifiers except for %J, %N, %n, %s, and %t. This holds
true even if '\\' is present, making it impossible to 'undo' the expansions
performed by scontrol. Additionally, the special specifier '%%' is expanded by
scontrol, so we cannot determine if a % was originally a specifier. For example,
%%J becomes %J in scontrol, but we cannot know its original form.
"""


def expand_stdout(scontrol_data):
    filename = scontrol_data["std_out"]
    if "\\" in filename:
        return filename
    filename = replace_jobid(filename, scontrol_data["job_id"])
    filename = replace_hostname(filename, scontrol_data["batch_host"])
    filename = replace_node_id(filename, node_id=0)
    filename = replace_stepid(filename, step_id="batch")
    filename = replace_taskid(filename, task_id=0)
    return filename


# Example usage
if __name__ == "__main__":
    filename = "\\%J_%N_%n_%s_%t"
    print(filename)
    if "\\" in filename:
        print("No expansion needed")

    filename = "%J_%N_%n_%s_%t"
    print(filename)
    filename = replace_jobid(filename, job_id="47")
    print(filename)
    filename = replace_hostname(filename, hostname="host1")
    print(filename)
    filename = replace_node_id(filename, node_id="1")
    print(filename)
    filename = replace_stepid(filename, step_id="step1")
    print(filename)
    filename = replace_taskid(filename, task_id="2")
    print(filename)
