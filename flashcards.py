from numpy import dtype
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
            fc_df.loc[row.name] = fc_row

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

def show_status(fc_df: pd.DataFrame):
    tot = len(fc_df)
    nums = [len(fc_df[fc_df['status']==x]) for x in [-1, 0, 1]]

    print(colored(f'\nTotal words   : {tot}\n', 'blue'))
    print(colored(f'Mastered      : {nums[2]}', 'green'))
    print(colored(f'Learning      : {nums[1]}', 'yellow'))
    print(colored(f'Remaining     : {nums[0]}', 'red'))

def wt_func(val, weights):
    if val==1:
        return weights.good
    elif val==0:
        return weights.neutral
    elif val==-1:
        return weights.bad
    else:
        raise ValueError('Invalid status value, must be one of {-1, 0, 1}')

def flashcards_(card: pd.Series, fc_df: pd.DataFrame, n_meanings: int, config: Namespace) -> None:
    fc_row = fc_df.loc[card.name]
    status_str = get_status_str(fc_row['status'])

    print(colored(card.name[0], config.status_colors.get(status_str)))
    print(colored(card.name[1], config.status_colors.get(status_str)))

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

        

        fc_row['count'] += 1
        fc_row['current'] = fc_row['current'] + 1 if correct else 0

        assert fc_row['current'] >= 0, 'Something is wrong. Current underflow.'

        if fc_row['current'] == 0:
            fc_row['status'] = -1
        elif fc_row['current'] > config.learn_threshold:
            fc_row['status'] = 1
        else:
            fc_row['status'] = 0

        fc_df.loc[card.name] = fc_row

    except KeyboardInterrupt:
        print('Cancelled.')
        raise LearningOverException

    finally:
        print('\n' + '-'*80 + '\n')

def flashcards(df: pd.DataFrame, fc_df: pd.DataFrame, config: Namespace) -> None:
    n_meanings = len(df.columns)

    try:
        while True:
            wts = fc_df['status'].apply(wt_func, weights=config.learn_weights)
            idx = fc_df.sample(weights=wts).iloc[0]
            flashcard = df.loc[idx.name]
            flashcards_(flashcard, fc_df, n_meanings, config)
    except LearningOverException:
        print('Learning Over.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--status', action='store_true', help='Give status of current progression')
    args = parser.parse_args()

    save_path = 'data/meanings.csv'
    data_path ='data/flashcard_data.csv'
    config_path = 'data/config.json'

    with open(config_path, 'r') as f:
        config = Namespace(**json.load(f))

    df = pd.read_csv(save_path, index_col=['Word', 'Type'])
    fc_df = pd.read_csv(data_path, index_col=['Word', 'Type'], dtype={'count':int, 'current':int, 'status':int})

    if args.status:
        show_status(fc_df)
    else:
        update(df, fc_df)
        flashcards(df, fc_df, config)
        fc_df.to_csv(data_path)

        print('All done. Nice.')

if __name__ == '__main__':
    main()