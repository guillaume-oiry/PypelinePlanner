from arango import ArangoClient

import os
import shutil
import csv
import json
from pathlib import Path


def create_arango_database(
    hosts,
    dataset,
    datasets_instructions={},
    subjects_instructions={},
    sessions_instructions={},
    files_instructions={},
):

    if "DATA" not in os.listdir():
        os.mkdir("DATA")
    os.chdir("DATA")

    if dataset in os.listdir():
        shutil.rmtree(dataset)
    os.system(f"git clone https://github.com/OpenNeuroDatasets/{dataset}.git")
    os.chdir(dataset)

    client = ArangoClient(hosts=hosts)
    sys_db = client.db("_system", username="root", password="passwd")

    if sys_db.has_database(dataset):
        sys_db.delete_database(dataset)
    sys_db.create_database(dataset)

    db = client.db(dataset, username="root", password="passwd")
    graph = db.create_graph("graph")

    datasets = db.create_collection("datasets")
    subjects = db.create_collection("subjects")
    sessions = db.create_collection("sessions")
    files = db.create_collection("files")

    datasets_have_subjects = graph.create_edge_definition(
        edge_collection="datasets_have_subjects",
        from_vertex_collections=["datasets"],
        to_vertex_collections=["subjects"],
    )
    subjects_in_datasets = graph.create_edge_definition(
        edge_collection="subjects_in_datasets",
        from_vertex_collections=["subjects"],
        to_vertex_collections=["datasets"],
    )
    subjects_have_sessions = graph.create_edge_definition(
        edge_collection="subjects_have_sessions",
        from_vertex_collections=["subjects"],
        to_vertex_collections=["sessions"],
    )
    sessions_of_subjects = graph.create_edge_definition(
        edge_collection="sessions_of_subjects",
        from_vertex_collections=["sessions"],
        to_vertex_collections=["subjects"],
    )
    datasets_have_sessions = graph.create_edge_definition(
        edge_collection="datasets_have_sessions",
        from_vertex_collections=["datasets"],
        to_vertex_collections=["sessions"],
    )
    sessions_have_files = graph.create_edge_definition(
        edge_collection="sessions_have_files",
        from_vertex_collections=["sessions"],
        to_vertex_collections=["files"],
    )

    # DATASET

    with open("dataset_description.json") as json_file:
        dataset_description = json.load(
            json_file
        )  # "Every [BIDS] dataset MUST include this file"

        dict_conversion(d=dataset_description, instructions=datasets_instructions)
        dataset_key = dataset
        datasets.insert(
            {"_key": dataset_key, "dataset_id": dataset, **dataset_description}
        )

    # SUBJECTS

    if "participants.tsv" in os.listdir():
        with open(
            "participants.tsv", newline=""
        ) as f:  # "If this file exists, it MUST contain the column participant_id"
            subjects_tsv = csv.DictReader(f, delimiter="\t")
            subjects_dict = {
                subject.pop("participant_id"): subject for subject in subjects_tsv
            }
    else:
        subjects_dict = {
            sub_id: {}
            for sub_id in [
                sub_id for sub_id in os.listdir() if sub_id.startswith("sub-")
            ]
        }

    for subject_id, subject_row in subjects_dict.items():

        dict_conversion(d=subject_row, instructions=subjects_instructions)
        subject_key = subject_id
        subjects.insert(
            {"_key": subject_key, "participant_id": subject_id, **subject_row}
        )

        datasets_have_subjects.link(
            f"datasets/{dataset_key}", f"subjects/{subject_key}"
        )
        subjects_in_datasets.link(f"subjects/{subject_key}", f"datasets/{dataset_key}")

        # SESSIONS

        os.chdir(subject_id)
        if f"{subject_id}_sessions.tsv" in os.listdir():
            with open(
                f"{subject_id}_sessions.tsv", newline=""
            ) as f:  # "If this file exists, it MUST contain the column session_id"
                sessions_tsv = csv.DictReader(f, delimiter="\t")
                sessions_dict = {
                    session.pop("session_id"): session for session in sessions_tsv
                }
        else:
            sessions_dict = {
                f"{subject_id}_{session_id}": {}
                for session_id in [
                    session_id
                    for session_id in os.listdir()
                    if session_id.startswith("ses-")
                ]
            }

        for session_id, session_row in sessions_dict.items():

            dict_conversion(d=session_row, instructions=sessions_instructions)
            session_key = f"{subject_id}_{session_id}"
            sessions.insert(
                {"_key": session_key, "session_id": session_id, **session_row}
            )

            subjects_have_sessions.link(
                f"subjects/{subject_key}", f"sessions/{session_key}"
            )
            sessions_of_subjects.link(
                f"sessions/{session_key}", f"subjects/{subject_key}"
            )
            datasets_have_sessions.link(
                f"datasets/{dataset_key}", f"sessions/{session_key}"
            )

            # FILES

            os.chdir(session_id.split("_")[1])
            path_list = list_files_pathlib(ls=[])
            files_dict = {filename: {} for filename in path_list}
            if f"{session_id}_scans.tsv" in os.listdir():
                with open(
                    f"{session_id}_scans.tsv", newline=""
                ) as f:  # "If this file exists, it MUST contain the column filename"
                    files_tsv = csv.DictReader(f, delimiter="\t")
                    files_description = {
                        file.pop("filename"): file for file in files_tsv
                    }
                files_dict.update(files_description)

            for filename, file_row in files_dict.items():
                dict_conversion(d=file_row, instructions=files_instructions)
                file_key = f"{session_id}_{filename.replace("/", "_")}"
                filepath = f"{session_id.replace("_", "/")}/{filename}"
                files.insert(
                    {
                        "_key": file_key,
                        "filename": filename,
                        "filepath": filepath,
                        **file_row,
                    }
                )

                sessions_have_files.link(f"sessions/{session_key}", f"files/{file_key}")

            os.chdir("..")

        os.chdir("..")

    os.chdir("..")
    shutil.rmtree(dataset)
    os.chdir("..")


def dict_conversion(d, instructions):
    for old_name, (new_name, new_type) in instructions.items():

        if old_name not in d.keys():
            continue

        if type(new_type) is str:
            match new_type:
                case "str":
                    d[new_name] = str(d.pop(old_name))
                case "int":
                    d[new_name] = int(d.pop(old_name))
                case "float":
                    d[new_name] = float(d.pop(old_name))
                case _:
                    raise Exception(
                        f"{new_type} is not a valid argument. Must choose between int, float and str; or use a dict."
                    )

        if type(new_type) is dict:
            d[new_name] = new_type[d.pop(old_name)]


def list_files_pathlib(path=Path("."), ls=[]):
    for entry in path.iterdir():
        if entry.is_file():
            ls.append(str(entry))
        elif entry.is_dir():
            list_files_pathlib(path=entry, ls=ls)
    return ls
