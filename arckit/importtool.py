import glob
import ujson # dumps minified by default
import os
import argparse


def import_arc_agi_2(repo_path, commit_hash):
    train_files = sorted(glob.glob(f'{repo_path}/data/training/*.json'))
    eval_files = sorted(glob.glob(f'{repo_path}/data/evaluation/*.json'))

    print(f"Found {len(train_files)} train tasks, {len(eval_files)} eval tasks")

    data = {"train": {}, "eval": {}}
    for json_file in train_files:
        taskname = os.path.basename(json_file).split('.')[0]
        taskdata = ujson.load(open(json_file))
        data['train'][taskname] = taskdata

    for json_file in eval_files:
        taskname = os.path.basename(json_file).split('.')[0]
        taskdata = ujson.load(open(json_file))
        data['eval'][taskname] = taskdata

    output_path = f"{os.path.dirname(__file__)}/data/arcagi2_{commit_hash}.json"

    ujson.dump(data, open(output_path, "w"))

def import_kaggle_2025(repo_path, id):
    train_challenges = ujson.load(open(f'{repo_path}/arc-agi_training_challenges.json', 'r'))
    eval_challenges = ujson.load(open(f'{repo_path}/arc-agi_evaluation_challenges.json', 'r'))
    train_solutions = ujson.load(open(f'{repo_path}/arc-agi_training_solutions.json', 'r'))
    eval_solutions = ujson.load(open(f'{repo_path}/arc-agi_evaluation_solutions.json', 'r'))

    # Populate the solutions into the challenges
    train_data = {}
    for challenge, challenge_data in train_challenges.items():
        challenge_test = train_solutions[challenge]
        for i, test in enumerate(challenge_test):
            challenge_data['test'][i]['output'] = test

        train_data[challenge] = challenge_data

    eval_data = {}
    for challenge, challenge_data in eval_challenges.items():
        challenge_test = eval_solutions[challenge]
        for i, test in enumerate(challenge_test):
            challenge_data['test'][i]['output'] = test

        eval_data[challenge] = challenge_data

    data = {"train": train_data, "eval": eval_data}

    output_path = f"{os.path.dirname(__file__)}/data/kaggle2025_{id}.json"
    ujson.dump(data, open(output_path, "w"))
        

def compare_json(json1="arckit/data/kaggle2025_250808.json", json2="arckit/data/arcagi2_f3283f7.json"):
    json1 = ujson.load(open(json1, "r"))
    json2 = ujson.load(open(json2, "r"))
    assert len(json1['train']) == len(json2['train'])
    assert len(json1['eval']) == len(json2['eval'])
    for k, v in json1['train'].items():
        if k not in json2['train']:
            print(k, "missing")
        if str(json2['train'][k]) != str(v):
            print(k, "not matching")
    for k, v in json2['eval'].items():
        if k not in json1['eval']:
            print(k, "missing")
        if str(json1['eval'][k]) != str(v):
            print(k, "not matching")
    exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--arcagi2', action="store_true")
    parser.add_argument('--kaggle2025', action="store_true")
    parser.add_argument('--repo-path')
    parser.add_argument('--id')
    args = parser.parse_args()

    if args.arcagi2:
        import_arc_agi_2(args.repo_path, args.id)
    elif args.kaggle2025:
        import_kaggle_2025(args.repo_path, args.id)
    else:
        print("Unknown importer.")