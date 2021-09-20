import argparse
import enum
import random
from termcolor import colored

class TopicStatus(enum.Enum):
    statement = 1
    instruction = 2

class LineType(enum.Enum):
    para = 1
    div = 2
    _div = 3
    other = 4

class Topic:
    def __init__(self):
        self.statement = []
        self.instruction = None
        self.status = TopicStatus.statement

    def update(self, line: str) -> bool:
        line_type = Topic.get_line_type(line)
        if self.status == TopicStatus.statement:
            if line_type == LineType.para:
                self.statement.append(line[3:-4])
            elif self.statement: # statement not empty
                if line_type == LineType.div:
                    self.status = TopicStatus.instruction
            return False
        elif self.status == TopicStatus.instruction:
            if line_type == LineType.para:
                self.instruction = line[3:-4]
            return True

    def __str__(self):
        bld = ''
        for s in self.statement:
            bld += s + '\n'
        bld = colored(bld, 'yellow')
        bld += colored('\n' + self.instruction + '\n', 'blue', on_color='on_yellow')
        return bld

    @staticmethod
    def get_line_type(line: str) -> LineType:
        if line[:3] == '<p>':
            return LineType.para
        elif line[:4] == '<div':
            return LineType.div
        elif line[-6:] == '</div>':
            return LineType._div
        else:
            return LineType.other

class TopicBuffer:
    def __init__(self):
        self.empty = True
        self.topic = None
        self.topic_db = []

    def build(self, line):
        if self.empty:
            self.topic = Topic()
            self.empty = False
        topic_complete = self.topic.update(line)
        if topic_complete:
            self.topic_db.append(self.topic)
            self.topic = None
            self.empty = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--issue-filename', default='issue_pool.txt', help='Name of the file to be read for the issue pool', metavar='')
    parser.add_argument('--argument-filename', default='argument_pool.txt', help='Name of the file to be read for the argument pool', metavar='')
    parser.add_argument('-i', '--issue', action='store_true', help='Select if you want an `issue` task')
    parser.add_argument('-a', '--argument', action='store_true', help='Select if you want an `argument` task')
    args = parser.parse_args()

    assert not (args.issue and args.argument), 'You can only request one of `issue` or `argument` task'

    if args.argument:
        issue = False
    elif args.issue:
        issue = True
    else:
        print('No option between `issue` and `argument` chosen. Selecting `issue` by default.')
        issue = True

    if issue:
        filename = args.issue_filename
    else:
        filename = args.argument_filename

    data_path = 'data/' + filename

    with open(data_path, 'r') as f:
        tb = TopicBuffer()
        for line in f:
            line = line.rstrip()
            tb.build(line)
        print(f'Total topics built: {len(tb.topic_db)}')

    topic = random.choice(tb.topic_db)
    print('\n\n' + '-'*80 + '\n')
    print(topic)
    print('\n' + '-'*80 + '\n')


if __name__ == '__main__':
    main()