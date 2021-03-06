import warnings
warnings.simplefilter(action='ignore')

import pandas as pd
import argparse
import json
from namespace import Namespace
from termcolor import colored

class LearningOverException(Exception):
    pass

def update(df: pd.DataFrame, fc_df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        try:
            fc_df.loc[row.name]
        except KeyError:
            fc_row = {'count' : 0, 'current' : 0, 'status' : 0}
            fc_df.loc[row.name, :] = fc_row

    for _, row in fc_df.iterrows():
        try:
            df.loc[row.name]
        except KeyError:
            fc_df.drop(index=row.name, inplace=True)

def get_status_str(status: int):
    if status==1:
        return 'good'
    elif status==0:
        return 'neutral'
    elif status==-1:
        return 'bad'
    else:
        raise ValueError('Invalid status value, must be one of {-1, 0, 1}')

def print_colored(s: str, color: str, no_color: bool = False) -> None:
    if no_color:
        print(s)
    else:
        print(colored(s, color))

def show_status(fc_df: pd.DataFrame, no_color: bool = False) -> None:
    tot = len(fc_df)
    nums = [len(fc_df[fc_df['status']==x]) for x in [-1, 0, 1]]

    print_colored(f'\nTotal words   : {tot}\n', 'blue', no_color)
    print_colored(f'Mastered      : {nums[2]}', 'green', no_color)
    print_colored(f'Learning      : {nums[1]}', 'yellow', no_color)
    print_colored(f'Remaining     : {nums[0]}', 'red', no_color)

def wt_func(val, weights):
    if val==1:
        return weights.good
    elif val==0:
        return weights.neutral
    elif val==-1:
        return weights.bad
    else:
        raise ValueError('Invalid status value, must be one of {-1, 0, 1}')

def flashcards_(card: pd.Series, fc_df: pd.DataFrame, n_meanings: int, config: Namespace, no_color: bool = False) -> None:
    fc_row = fc_df.loc[card.name]
    status_str = get_status_str(fc_row['status'])

    print_colored(card.name[0], config.status_colors.get(status_str), no_color)
    print_colored(card.name[1], config.status_colors.get(status_str), no_color)

    try:
        correct = input('Press Enter to show meaning\n')

        for n in range(n_meanings):
            m = f'Meaning {n+1}'
            if not pd.isna(card[m]):
                print(f'{m} : {card[m]}')
            else:
                break

        print()

        try:
            correct = int(correct)
        except ValueError:
            correct = ''

        if correct=='':
            input_received = False
            correct = input('Press 0 for incorrect, any other number for correct.\n')

            while not input_received:
                try:
                    correct = int(correct)
                    input_received = True
                except ValueError:
                    correct = input('Invalid input. Please enter an integer value.\n')

        correct = bool(correct)

        fc_row.loc['count'] += 1
        fc_row.loc['session_tries'] += 1
        if correct:
            fc_row.loc['current'] += 1
            fc_row.loc['session_correct'] += 1
        else:
            fc_row.loc['current'] = 0

        assert fc_row.loc['current'] >= 0, 'Something is wrong. Current underflow.'

        if fc_row.loc['current'] == 0:
            fc_row.loc['status'] = -1
        elif fc_row.loc['current'] >= config.learn_threshold:
            fc_row.loc['status'] = 1
        else:
            fc_row.loc['status'] = 0

        fc_df.loc[card.name, :] = fc_row
        print('\n' + '-'*80 + '\n')
        return fc_df

    except KeyboardInterrupt:
        print('Cancelled.')
        raise LearningOverException

def flashcards(df: pd.DataFrame, fc_df: pd.DataFrame, config: Namespace, args: argparse.Namespace) -> None:
    n_meanings = len(df.columns)

    group_num = args.group_num
    no_color =args.no_color

    if group_num is None:
        num_grps = (n_meanings - 1) // config.group_size + 1
        selected_grp = 0
        max_not_learned = 0
        for group in range(num_grps):
            grp_start = group * config.group_size
            grp_end = (group + 1) * config.group_size
            not_learned = fc_df.iloc[grp_start: grp_end]['status'].apply(lambda x: 1 if x < 1 else 0).sum()
            if not_learned > max_not_learned:
                max_not_learned = not_learned
                selected_grp = group

        group_num = selected_grp

    print(f'Doing grp {group_num}\n')

    grp_start = group_num * config.group_size
    grp_end = (group_num + 1)* config.group_size

    fc_grp = fc_df.iloc[grp_start: grp_end]
    fc_grp['session_tries'] = 0
    fc_grp['session_correct'] = 0

    try:
        while True:
            wts = fc_grp['status'].apply(wt_func, weights=config.learn_weights)
            idx = fc_grp.sample(weights=wts).iloc[0]
            flashcard = df.loc[idx.name]
            fc_ret = flashcards_(flashcard, fc_grp, n_meanings, config, no_color=no_color)
            fc_grp.update(fc_ret)
    except LearningOverException:
        print('Learning Over.')
    finally:
        show_session_data(fc_grp)
        fc_df.update(fc_grp)

def show_session_data(fc_df: pd.DataFrame) -> None:
    tot_tries = fc_df['session_tries'].sum()
    tot_correct = fc_df['session_correct'].sum()
    tot_words = len(fc_df)
    words_tried = fc_df['session_tries'].apply(lambda x: 1 if x > 0 else 0).sum()

    print(f'Number of words in grp                  : {tot_words}')
    print(f'Number of words appeared in session     : {words_tried}')
    print(f'Total tries in the session              : {tot_tries}')
    print(f'Total correct answers in the session    : {tot_correct}')

    response = input('Enter 1 to show details. Enter anything else to exit.\n')

    if response=='1':
        print(fc_df)
    else:
        print('Exiting')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--status', action='store_true', help='Give status of current progression')
    parser.add_argument('-g', '--group-num', default=None, type=int, help='Option to practice a particular group', metavar='')
    parser.add_argument('--no-color', action='store_true', help='Remove colored outputs if they are not displaying properly')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle the order of words and their groups.')
    args = parser.parse_args()

    save_path = 'data/meanings.csv'
    data_path ='data/flashcard_data.csv'
    config_path = 'data/config.json'

    with open(config_path, 'r') as f:
        config = Namespace(**json.load(f))

    df = pd.read_csv(save_path, index_col=['Word', 'Type'])
    fc_df = pd.read_csv(data_path, index_col=['Word', 'Type'], dtype={'count':int, 'current':int, 'status':int})

    update(df, fc_df)

    if args.shuffle:
        fc_df = fc_df.sample(frac=1.)
        fc_df.to_csv(data_path)
        print('Shuffle complete.')
        return
    
    if args.status:
        show_status(fc_df, args.no_color)
    else:
        flashcards(df, fc_df, config, args=args)

    fc_df.to_csv(data_path)
    print('All done. Nice.')

if __name__ == '__main__':
    main()