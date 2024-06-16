from glob import glob
import json
import numpy as np
import os
import csv

from rich.traceback import install
install()#(show_locals=True)

from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def idx2chr(idx):
    return chr(idx + 65)

def fmt_grid(grid, colour=True, spaces=True):
    grid_str = []
    if not colour:
        for row in grid:
            if spaces == 'gpt':
                grid_str.append(''.join([' ' + str(x) for x in row]))
            elif spaces:
                grid_str.append(' '.join([str(x) for x in row]))
            else:
                grid_str.append(''.join([str(x) for x in row]))

        return "\n".join(grid_str)
    else:
        if spaces:
            cmap = dict({i: (str(i) + ' ', f"color({i})") for i in range(10)}, **{str(i): (str(i) + ' ', f"color({i})") for i in range(10)})
        else:
            cmap = dict({i: (str(i), f"color({i})") for i in range(10)}, **{str(i): (str(i), f"color({i})") for i in range(10)})

        for row in grid:
            grid_str += [cmap[digit] for digit in row]
            grid_str += ["\n"]

        return Text.assemble(*grid_str[:-1])

class Task:
    def __init__(self, id, train, test, dataset=None):
        self.dataset = dataset
        self.id = id
        self.train = [(np.array(example['input']), np.array(example['output'])) for example in train]
        self.test = [(np.array(example['input']), np.array(example['output'])) for example in test]

        self.color_count = max

    def __lt__(self, other):
        return self.id < other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def from_json(cls, json_file):
        with open(json_file) as f:
            data = json.load(f)

            # train_examples = [(np.array(example['input']), np.array(example['output'])) for example in data['train']]
            # test_examples = [(np.array(example['input']), np.array(example['output'])) for example in data['test']]

            return cls(os.path.basename(json_file)[:-5], data['train'], data['test'])

    def __repr__(self):
        return f"<Task-{self.dataset} {self.id} | {len(self.train)} train | {len(self.test)} test>"

    def show(self, answer=False):
        table = Table(title=repr(self), show_lines=True)

        data = []
        for i, (input, output) in enumerate(self.train):
            data += [fmt_grid(input), fmt_grid(output)]
            ix, iy = input.shape
            ox, oy = output.shape
            table.add_column(f"{idx2chr(i)}-in {ix}x{iy}", justify="center", no_wrap=True)
            table.add_column(f"{idx2chr(i)}-out {ox}x{oy}", justify="center", no_wrap=True)

        data.append('')
        table.add_column("")
        for i, (input, output) in enumerate(self.test):
            table.add_column(f"T{idx2chr(i)}-in", justify="center", header_style="bold", no_wrap=True)
            if answer:
                table.add_column(f"T{idx2chr(i)}-out", justify="center", header_style="bold", no_wrap=True)
                data += [fmt_grid(input), fmt_grid(output)]
            else:
                data += [fmt_grid(input)]

        table.add_row(*data)
        print(table)
        return table

    def to_dict(self):
        return {
            "id": self.id,
            "train": [{"input": input.tolist(), "output": output.tolist()} for input, output in self.train],
            "test": [{"input": input.tolist(), "output": output.tolist()} for input, output in self.test]
        }
    
    def dreamcoder_format(self):
        # TODO: Separate out the train/test data
        # Currently, dreamcoder gets to search on the train examples too
        # This is included to keep compatibility with Simon's results, but should be corrected and written about
        grids = []
        for inp, out in self.train:
            grids += [inp, out]
        for inp, out in self.test:
            grids += [inp, out]
        return {"name": self.id, "grids": grids}

    def scoreA(self, output):
        output = np.array(output).astype(int)
        if output.shape != self.test[0][1].shape:
            return False
        return (output == self.test[0][1]).all()

    def gpt_prompt(self, i_test, mode="chatgpt", include_completion=False, rot90=False, transpose=False, spaces=True):
        if mode == "chatgpt":
            prompt = "We are playing a game which involves transforming an input grid of digits into an output grid of digits. In general, digits form objects in 2D and the task is to perform some spatial transformation of these objects to go from the input grid to the output grid. All the information about the transformation is contained within the input pairs themselves, and your answer will only be correct if the output grid is exactly correct, so this is what I expect from you. I will begin by giving you several examples of input-output pairs. You will then be given a new input grid, and you must provide the corresponding output grid.\n"
        elif mode == "gpt3":
            # prompt = "We are playing a game which involves transforming an input grid of digits into an output grid of digits. Every below pair of grids contains the same transformation. In general, digits form objects in 2D and the task is to perform some spatial transformation of these objects to go from the input tile to the output tile. One such example of tiles is below.\n"
            prompt = "We are playing a game which involves transformaing a 2D input grid of digits into an output grid of digits. Every below pair of grids contains the same transformation (e.g. rotation, symmetry, manipulation of objects). Each Input grid is followed by an Output grid which applies the same transformation as previous Input/Output pairs. One such example is below.\n"
        else:
            raise ValueError(f"Unknown mode: {mode}")

        i = 1
        for input, output in self.train:
            if rot90:
                input = np.rot90(input)
                output = np.rot90(output)
            if transpose:
                input = np.transpose(input)
                output = np.transpose(output)

            prompt += f"""Input {i}: 
{fmt_grid(input, colour=False, spaces=spaces)}
Output {i}: 
{fmt_grid(output, colour=False, spaces=spaces)}\n
"""
            i += 1

        test_grid = self.test[i_test][0]
        if rot90:
            test_grid = np.rot90(test_grid)
        if transpose:
            test_grid = np.transpose(test_grid)

        prompt += f"Input {i}:\n"
        prompt += f"{fmt_grid(test_grid, colour=False, spaces=spaces)}"
        if mode == "gpt3":
            prompt += f"\nOutput {i}:"
        else:
            prompt += f"\nOutput {i}: (please provide the output grid only)\n"

        if include_completion:
            if rot90:
                output = np.rot90(self.test[i_test][1])
            if transpose:
                output = np.transpose(self.test[i_test][1])
            prompt += f"\n{fmt_grid(self.test[i_test][1], colour=False, spaces=spaces)}"
        return prompt

class TaskSet:
    def __init__(self, tasks):
        tasks = sorted(tasks)
        self.tasks = tasks
        self.task_dict = {task.id: task for task in tasks}

    def __getitem__(self, item):
        if isinstance(item, slice):
            return TaskSet(self.tasks[item])
        get = self.task_dict.get(item)
        if get is None:
            try:
                return self.tasks[item]
            except (TypeError, IndexError):
                raise KeyError(f"Task {item} not found")
        return get

    def __len__(self):
        return len(self.tasks)

    def __iter__(self):
        return iter(self.tasks)

    def __repr__(self):
        return f"<TaskSet: {len(self.tasks)} tasks>"

    def score_submission(self,fn: str, topn=3, return_correct=False) -> int:
        """
        Score a submission file, in Kaggle csv format
        Two columns: output_id,output
        """
        from collections import defaultdict
        preds = defaultdict(list)

        with open(fn) as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_id, test_num = row['output_id'].split('_')
                test_num = int(test_num)
                assert test_num == len(preds[task_id]), f'Predictions must be in order'
                 # Predictions must be in order

                row_preds = row['output'].strip().split(' ')
                row_preds = row_preds[:topn] # max 3 preds

                try:
                    array_preds = []
                    for p in row_preds:
                        p = p.strip('|').split('|')
                        p = [[int(x) for x in row] for row in p]
                        array_preds.append(np.array(p))
                except:
                    raise ValueError(f'Could not parse prediction: {row_preds}')

                preds[task_id].append(array_preds)

        total_score = 0
        correct = set()
        for task in self.tasks:
            test_examples = task.test
            assert len(test_examples) == len(preds[task.id])

            score = 0
            for ex, ex_preds in zip(test_examples, preds[task.id]):
                if any([np.array_equal(ex[1], pred) for pred in ex_preds]):
                    score += 1

            if score == len(test_examples):
                total_score += 1
                correct.add(task.id)

        if return_correct:
            return total_score, correct
        else:
            return total_score
        

def load_data() -> (TaskSet, TaskSet):
    train_data = json.load(open(f"{os.path.dirname(__file__)}/arc-agi_training_challenges.json"))
    train_solutions = json.load(open(f"{os.path.dirname(__file__)}/arc-agi_training_solutions.json"))
    eval_data = json.load(open(f"{os.path.dirname(__file__)}/arc-agi_evaluation_challenges.json"))
    eval_solutions = json.load(open(f"{os.path.dirname(__file__)}/arc-agi_evaluation_solutions.json"))
    train_tasks = []
    eval_tasks = []
    
    for id in train_data:
        task = train_data[id]
        solution = train_solutions[id]
        
        for i in range(len(solution)):
            task['test'][i]['output'] = solution[i]
        train_tasks.append(Task(id, task['train'], task['test'], 'train'))
    
    for id in eval_data:
        task = eval_data[id]
        solution = eval_solutions[id]
        for i in range(len(solution)):
            task['test'][i]['output'] = solution[i]
        eval_tasks.append(Task(id, task['train'], task['test'], 'train'))
        
    return TaskSet(train_tasks), TaskSet(eval_tasks)

def load_single(id: str) -> Task:
    """
    Load a single task from disk.
    """
    data = json.load(open(f"{os.path.dirname(__file__)}/arc1.json"))
    # task = data['train'][id]
    # return Task(id, task['train'], task['test'], 'train'
    if id.startswith('train'):
        dataset_tasks = sorted(data['train'].items())
        taskid, task = dataset_tasks[int(id[5:])]
        return Task(taskid, task['train'], task['test'], 'train')
    elif id.startswith('eval'):
        dataset_tasks = sorted(data['eval'].items())
        taskid, task = dataset_tasks[int(id[4:])]
        return Task(taskid, task['train'], task['test'], 'eval')
    elif id in data['train']:
        task = data['train'][id]
        return Task(id, task['train'], task['test'], 'train')
    elif id in data['eval']:
        task = data['eval'][id]
        return Task(id, task['train'], task['test'], 'eval')
    else:
        raise ValueError(f"Unknown task id: {id}")

if __name__ == "__main__":
    train_tasks, eval_tasks = load_data()
    print(train_tasks)
    print(eval_tasks)
    print(train_tasks["007bbfb7"])
    for i in range(10):
        train_tasks[i].show()

    print(train_tasks["08ed6ac7"].gpt_prompt("gpt3"))